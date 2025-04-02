#
# Blue Brain Nexus Forge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Blue Brain Nexus Forge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Blue Brain Nexus Forge. If not, see <https://choosealicense.com/licenses/lgpl-3.0/>.
from typing import Dict, Optional, Union, List, Tuple

import json
import requests
from urllib.parse import quote_plus

from rdflib import URIRef, Namespace, Graph, RDF, SH
from rdflib import Dataset as RDFDataset

from kgforge.core.commons.exceptions import RetrievalError
from kgforge.core.commons.sparql_query_builder import (
    build_ontology_query,
    build_shacl_query,
)
from kgforge.core.conversions.rdf import as_jsonld
from kgforge.core.archetypes.store import Store
from kgforge.specializations.models.rdf.node_properties import NodeProperties
from kgforge.specializations.models.rdf.service import RdfService
from kgforge.specializations.stores.nexus import Service


class StoreService(RdfService):

    def __init__(
        self,
        default_store: Store,
        context_iri: Optional[str] = None,
        context_store: Optional[Store] = None,
    ) -> None:

        self.default_store = default_store
        self.context_store = context_store or default_store
        # FIXME: define a store independent strategy
        self.store_metadata_iri = (
            self.default_store.service.store_context
            if hasattr(self.default_store.service, "store_context")
            else Namespace(Service.NEXUS_CONTEXT_FALLBACK)
        )
        super().__init__(RDFDataset(), context_iri)

    def schema_source_id(self, shape_uri: str) -> str:
        return str(self.shape_to_defining_resource[URIRef(shape_uri)])

    def materialize(self, iri: URIRef) -> NodeProperties:
        shape, _, _ = self.get_shape_graph(iri)
        predecessors = set()
        props, attrs = shape.traverse(predecessors)
        if props:
            attrs["properties"] = props
        return NodeProperties(**attrs)

    def resolve_context(self, iri: str) -> Dict:
        if iri in self._context_cache:
            return self._context_cache[iri]
        document = self.recursive_resolve(iri)
        self._context_cache.update({iri: document})
        return document

    def generate_context(self) -> Dict:
        for shape_uriref, schema_uriref in self.shape_to_defining_resource.items():
            if schema_uriref not in self._imported:
                self._transitive_load_resource_graph(
                    self._get_named_graph_from_shape(shape_uriref), schema_uriref
                )
        # reloads the shapes graph
        self._init_shape_graph_wrapper()
        return self._generate_context()

    def _build_shapes_map(self) -> Tuple[Dict, Dict, Dict]:
        base_url = f"{self.context_store.endpoint}/schemas/{self.context_store.bucket}"
        schemas_url = f"{base_url}?deprecated=false"
        response = requests.get(schemas_url)
        response.raise_for_status()
        context_document = self.context.document
        shape_list = response.json()

        class_to_shape = {}
        shape_to_defining_resource = {}
        defining_resource_to_named_graph = {}
        graph = Graph()

        for shape in shape_list["_results"]:
            shape_id = shape["@id"]
            shape_url = f"{base_url}/{quote_plus(shape_id)}"
            shape_response = requests.get(shape_url)
            shape_response.raise_for_status()
            shape_data = shape_response.json()
            shape_data["@context"] = context_document
            try:

                graph.parse(data=str(shape_data), format="json-ld")
            except Exception:
                # Fallback: Convert JSON-LD manually into RDF triples
                for shape in shape_data.get("shapes", []):
                    inner_shape_id = URIRef(self.context.expand(shape["@id"]))
                    shape_type = shape["@type"]
                    if shape_type == "NodeShape":
                        shape_type = SH.NodeShape
                    target_class = URIRef(self.context.expand(shape["targetClass"]))

                    # Add to graph
                    graph.add((URIRef(shape_id), self.NXV.shapes, URIRef(inner_shape_id)))
                    graph.add((inner_shape_id, URIRef(RDF.type), shape_type))
                    graph.add((inner_shape_id, URIRef(SH.targetClass), target_class))

                    for prop in shape.get("property", []):
                        path = URIRef(prop["path"])
                        graph.add((inner_shape_id, SH.property, path))

        graph.serialize(format="json-ld", destination="loaded_shapes.json")
        query = build_shacl_query(context_document)

        for row in graph.query(query):
            shape_uriref = URIRef(row.shape)
            class_to_shape[URIRef(row.targetClass)] = shape_uriref
            shape_to_defining_resource[shape_uriref] = URIRef(row.resource)
            defining_resource_to_named_graph[URIRef(row.resource)] = URIRef(f"{row.resource}/graph")

        return (
            class_to_shape,
            shape_to_defining_resource,
            defining_resource_to_named_graph,
        )

    def _build_ontology_map(self) -> Dict:
        query = build_ontology_query()
        limit = 1000
        offset = 0
        count = limit
        ont_to_named_graph = {}
        while count == limit:
            resources = self.context_store.sparql(
                query, debug=False, limit=limit, offset=offset
            )
            for r in resources:
                ont_uri = self.context.expand(r.ont)
                ont_uriref = URIRef(ont_uri)
                ont_to_named_graph[ont_uriref] = URIRef(ont_uri + "/graph")
            count = len(resources)
            offset += limit
        return ont_to_named_graph

    def recursive_resolve(self, context: Union[Dict, List, str]) -> Dict:
        document = {}
        if isinstance(context, list):
            if self.store_metadata_iri in context:
                context.remove(self.store_metadata_iri)
            if (
                hasattr(self.default_store.service, "store_local_context")
                and self.default_store.service.store_local_context in context
            ):
                context.remove(self.default_store.service.store_local_context)
            for x in context:
                document.update(self.recursive_resolve(x))
        elif isinstance(context, str):
            try:
                local_only = not self.default_store == self.context_store
                doc = self.default_store.service.resolve_context(
                    context, local_only=local_only
                )
            except ValueError:
                try:
                    doc = self.context_store.service.resolve_context(
                        context, local_only=False
                    )
                except ValueError as e:
                    raise e
            document.update(self.recursive_resolve(doc))
        elif isinstance(context, dict):
            document.update(context)
        return document

    def load_resource_graph_from_source(self, graph_id: str, schema_id: str) -> Graph:
        try:
            schema_resource = self.context_store.retrieve(
                schema_id, version=None, cross_bucket=False
            )
        except RetrievalError as e:
            raise ValueError(f"Failed to retrieve {schema_id}: {str(e)}") from e
        json_dict = as_jsonld(
            schema_resource,
            form="expanded",
            store_metadata=False,
            model_context=None,
            metadata_context=None,
            context_resolver=self.context_store.service.resolve_context,
        )
        schema_graph = self._dataset_graph.graph(URIRef(graph_id))
        schema_graph.remove((None, None, None))
        schema_graph.parse(data=json.dumps(json_dict), format="json-ld")
        return schema_graph
