# Neo4j import notes for GeoToxGraph

## Files

| File | Purpose |
| --- | --- |
| `neo4j_nodes.csv` | Neo4j node import file with `:ID`, `:LABEL`, and graph attributes. |
| `neo4j_relationships.csv` | Neo4j relationship import file with `:START_ID`, `:END_ID`, and `:TYPE`. |
| `geotoxgraph_nodes_enriched.csv` | Analysis-friendly enriched node table. |
| `geotoxgraph_edges_enriched.csv` | Analysis-friendly enriched edge table. |
| `geotoxgraph.graphml` | Directed GraphML export for Cytoscape, yEd, Gephi with GraphML support, or downstream graph tooling. |

## Neo4j admin import

For an empty Neo4j database, place the CSV files in the Neo4j import directory and run:

```bash
neo4j-admin database import full \
  --nodes=neo4j_nodes.csv \
  --relationships=neo4j_relationships.csv \
  neo4j
```

The relationship type comes from the edge predicate, uppercased and normalized. Examples include `HAS_MODULE`, `TRANSFORMED_TO`, `REDUCED_TO`, `EXPORTED_BY`, `MEMBER_OF`, and `PARTICIPATES_IN`.

## Cypher load option

For an existing database, use `LOAD CSV WITH HEADERS`. This approach is slower but easier to adapt:

```cypher
LOAD CSV WITH HEADERS FROM 'file:///neo4j_nodes.csv' AS row
CALL apoc.create.node(split(row.`:LABEL`, ';'), {
  id: row.`:ID`,
  name: row.name,
  node_type: row.node_type,
  strain_id: row.strain_id,
  module_id: row.module_id,
  entity_class: row.entity_class,
  identifier: row.identifier,
  description: row.description,
  source_url: row.source_url,
  kegg_gene_ids: row.kegg_gene_ids,
  ko_ids: row.ko_ids,
  ec_numbers: row.ec_numbers,
  kegg_pathways: row.kegg_pathways,
  kegg_modules: row.kegg_modules,
  ncbi_protein_ids: row.ncbi_protein_ids,
  uniprot_ids: row.uniprot_ids,
  pubchem_cid: row.pubchem_cid,
  kegg_compound: row.kegg_compound,
  chebi_id: row.chebi_id,
  metacyc_candidate: row.metacyc_candidate,
  metacyc_status: row.metacyc_status,
  annotation_status: row.annotation_status
}) YIELD node
RETURN count(node);
```

Then load relationships by matching on `id` and creating relationship types. APOC is recommended for dynamic relationship types.

## Recommended constraints

```cypher
CREATE CONSTRAINT geotoxgraph_node_id IF NOT EXISTS
FOR (n) REQUIRE n.id IS UNIQUE;
```

## Curation warning

MetaCyc fields are included as `metacyc_candidate` and `metacyc_status`. These are candidate labels, not validated BioCyc stable identifiers, unless a future curation pass explicitly marks them verified.
