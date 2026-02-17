#!/usr/bin/env python3
"""
Build GraphForge knowledge graph from OpenCypher feature documentation.

Creates a queryable graph database mapping:
- OpenCypher features
- Implementation status
- TCK test scenarios
- Feature categories and dependencies

Output: docs/feature-graph.db
"""

import re
import sys
from pathlib import Path

# Add parent directory to path to import graphforge
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from graphforge import GraphForge
except ImportError:
    print("Error: Could not import graphforge. Make sure it's installed.")
    print("Run: uv pip install -e .")
    sys.exit(1)


def parse_implementation_status(status_file):
    """Parse implementation status from markdown file."""
    features = []

    with open(status_file, 'r') as f:
        content = f.read()

    # Extract features with status markers
    # Pattern: ### FeatureName followed by **Status:** ✅/⚠️/❌
    pattern = r'###\s+(.+?)\n.*?\*\*Status:\*\*\s+(✅|⚠️|❌)\s+(COMPLETE|PARTIAL|NOT_IMPLEMENTED)'

    matches = re.finditer(pattern, content, re.DOTALL)

    for match in matches:
        feature_name = match.group(1).strip()
        emoji = match.group(2)
        status_text = match.group(3)

        # Map status
        if emoji == '✅' or 'COMPLETE' in status_text:
            status = 'complete'
        elif emoji == '⚠️' or 'PARTIAL' in status_text:
            status = 'partial'
        else:
            status = 'not_implemented'

        # Extract file reference if present
        file_match = re.search(r'\*\*File[s]?:\*\*\s+`?([^`\n]+)', content[match.end():match.end()+500])
        file_path = file_match.group(1) if file_match else None

        features.append({
            'name': feature_name,
            'status': status,
            'file_path': file_path
        })

    return features


def parse_clause_status():
    """Parse clause implementation status."""
    status_file = Path('docs/reference/implementation-status/clauses.md')
    if not status_file.exists():
        return []

    features = parse_implementation_status(status_file)

    # Add category
    for f in features:
        f['category'] = 'clause'
        f['subcategory'] = determine_clause_subcategory(f['name'])

    return features


def parse_function_status():
    """Parse function implementation status."""
    status_file = Path('docs/reference/implementation-status/functions.md')
    if not status_file.exists():
        return []

    features = parse_implementation_status(status_file)

    # Add category
    for f in features:
        f['category'] = 'function'
        f['subcategory'] = determine_function_subcategory(f['name'])

    return features


def parse_operator_status():
    """Parse operator implementation status."""
    status_file = Path('docs/reference/implementation-status/operators.md')
    if not status_file.exists():
        return []

    features = parse_implementation_status(status_file)

    # Add category
    for f in features:
        f['category'] = 'operator'
        f['subcategory'] = determine_operator_subcategory(f['name'])

    return features


def parse_pattern_status():
    """Parse pattern implementation status."""
    status_file = Path('docs/reference/implementation-status/patterns.md')
    if not status_file.exists():
        return []

    features = parse_implementation_status(status_file)

    # Add category
    for f in features:
        f['category'] = 'pattern'
        f['subcategory'] = 'pattern_matching'

    return features


def determine_clause_subcategory(name):
    """Determine clause subcategory."""
    name_lower = name.lower()
    if any(k in name_lower for k in ['match', 'optional']):
        return 'reading'
    elif any(k in name_lower for k in ['return', 'with', 'unwind']):
        return 'projecting'
    elif any(k in name_lower for k in ['create', 'merge', 'delete', 'set', 'remove']):
        return 'writing'
    elif any(k in name_lower for k in ['union']):
        return 'set_operations'
    else:
        return 'other'


def determine_function_subcategory(name):
    """Determine function subcategory."""
    name_lower = name.lower()
    if any(k in name_lower for k in ['substring', 'trim', 'upper', 'lower', 'split', 'replace', 'reverse', 'left', 'right', 'tostring']):
        return 'string'
    elif any(k in name_lower for k in ['abs', 'ceil', 'floor', 'round', 'sign', 'tointeger', 'tofloat', 'sqrt', 'rand']):
        return 'numeric'
    elif any(k in name_lower for k in ['size', 'head', 'tail', 'last', 'range', 'extract', 'filter', 'reduce']) and 'path' not in name_lower:
        return 'list'
    elif any(k in name_lower for k in ['count', 'sum', 'avg', 'min', 'max', 'collect', 'percentile', 'stdev']):
        return 'aggregation'
    elif any(k in name_lower for k in ['all', 'any', 'none', 'single', 'exists', 'isempty']):
        return 'predicate'
    elif any(k in name_lower for k in ['id', 'type', 'labels', 'properties', 'keys', 'coalesce', 'toboolean', 'timestamp']):
        return 'scalar'
    elif any(k in name_lower for k in ['date', 'datetime', 'time', 'localtime', 'localdatetime', 'duration', 'year', 'month', 'day', 'hour', 'minute', 'second', 'truncate']):
        return 'temporal'
    elif any(k in name_lower for k in ['point', 'distance']):
        return 'spatial'
    elif any(k in name_lower for k in ['length', 'nodes', 'relationships']) and 'path' not in name_lower.replace('length', ''):
        return 'path'
    else:
        return 'other'


def determine_operator_subcategory(name):
    """Determine operator subcategory."""
    name_lower = name.lower()
    if any(k in name_lower for k in ['equals', 'not equals', 'less', 'greater', 'is null']):
        return 'comparison'
    elif any(k in name_lower for k in ['and', 'or', 'not', 'xor']):
        return 'logical'
    elif any(k in name_lower for k in ['addition', 'subtraction', 'multiplication', 'division', 'modulo', 'power']):
        return 'arithmetic'
    elif any(k in name_lower for k in ['concatenation', 'regex', 'starts', 'ends', 'contains']):
        return 'string'
    elif any(k in name_lower for k in ['membership', 'index', 'slicing', 'list']):
        return 'list'
    else:
        return 'other'


def parse_tck_mappings():
    """Parse TCK scenario mappings from feature-mapping docs."""
    mappings = {}

    # Parse clause-to-tck mapping
    clause_file = Path('docs/reference/feature-mapping/clause-to-tck.md')
    if clause_file.exists():
        with open(clause_file, 'r') as f:
            content = f.read()

        # Extract mappings: ### FeatureName followed by **Total TCK Coverage:** N scenarios
        pattern = r'###\s+(.+?)\n.*?\*\*Total TCK Coverage:\*\*\s+(\d+)\s+scenarios'
        for match in re.finditer(pattern, content, re.DOTALL):
            feature_name = match.group(1).strip()
            scenario_count = int(match.group(2))
            mappings[feature_name] = scenario_count

    # Parse function-to-tck mapping
    function_file = Path('docs/reference/feature-mapping/function-to-tck.md')
    if function_file.exists():
        with open(function_file, 'r') as f:
            content = f.read()

        # Similar pattern for functions
        pattern = r'###\s+(.+?)\n.*?\*\*TCK Category.*?\n.*?\*\*Coverage by Function'
        # This is more complex, just estimate for now

    return mappings


def build_graph():
    """Build the GraphForge knowledge graph."""

    print("Building OpenCypher feature knowledge graph...")

    # Create graph database
    db_path = Path('docs/feature-graph.db')
    if db_path.exists():
        db_path.unlink()
        print(f"  Removed existing database: {db_path}")

    gf = GraphForge(str(db_path))
    print(f"  Created database: {db_path}")

    # Parse all features
    print("\nParsing feature documentation...")
    clauses = parse_clause_status()
    functions = parse_function_status()
    operators = parse_operator_status()
    patterns = parse_pattern_status()

    all_features = clauses + functions + operators + patterns
    print(f"  Found {len(all_features)} features:")
    print(f"    Clauses: {len(clauses)}")
    print(f"    Functions: {len(functions)}")
    print(f"    Operators: {len(operators)}")
    print(f"    Patterns: {len(patterns)}")

    # Parse TCK mappings
    tck_mappings = parse_tck_mappings()
    print(f"  Found {len(tck_mappings)} TCK mappings")

    # Create Category nodes
    print("\nCreating Category nodes...")
    categories = {
        'Reading Clauses': 'Query clauses for reading data from the graph',
        'Projecting Clauses': 'Query clauses for projecting and transforming results',
        'Writing Clauses': 'Query clauses for creating and modifying graph data',
        'Set Operations': 'Query clauses for combining results',
        'String Functions': 'Functions for string manipulation',
        'Numeric Functions': 'Functions for mathematical operations',
        'List Functions': 'Functions for list operations',
        'Aggregation Functions': 'Functions for aggregating values',
        'Predicate Functions': 'Functions for testing conditions',
        'Scalar Functions': 'Functions for scalar operations',
        'Temporal Functions': 'Functions for date and time operations',
        'Spatial Functions': 'Functions for spatial operations',
        'Path Functions': 'Functions for path operations',
        'Comparison Operators': 'Operators for comparing values',
        'Logical Operators': 'Operators for logical operations',
        'Arithmetic Operators': 'Operators for arithmetic operations',
        'String Operators': 'Operators for string operations',
        'List Operators': 'Operators for list operations',
        'Pattern Operators': 'Operators for pattern matching',
        'Pattern Matching': 'Pattern matching features'
    }

    category_nodes = {}
    for name, description in categories.items():
        node = gf.create_node(
            labels=['Category'],
            name=name,
            description=description
        )
        category_nodes[name] = node
        print(f"  Created: {name}")

    # Create Feature nodes
    print("\nCreating Feature nodes...")
    feature_nodes = {}
    for feature in all_features:
        node = gf.create_node(
            labels=['Feature'],
            name=feature['name'],
            category=feature['category'],
            subcategory=feature['subcategory']
        )
        feature_nodes[feature['name']] = node

    print(f"  Created {len(feature_nodes)} Feature nodes")

    # Create Implementation nodes
    print("\nCreating Implementation nodes...")
    impl_count = 0
    for feature in all_features:
        if feature.get('file_path'):
            impl_node = gf.create_node(
                labels=['Implementation'],
                file_path=feature['file_path'],
                status=feature['status']
            )

            # Create IMPLEMENTED_IN relationship
            feature_node = feature_nodes[feature['name']]
            gf.create_relationship(
                src=feature_node,
                dst=impl_node,
                rel_type='IMPLEMENTED_IN',
                completeness=1.0 if feature['status'] == 'complete' else 0.5 if feature['status'] == 'partial' else 0.0
            )
            impl_count += 1

    print(f"  Created {impl_count} Implementation nodes")

    # Create BELONGS_TO_CATEGORY relationships
    print("\nCreating category relationships...")
    category_map = {
        'reading': 'Reading Clauses',
        'projecting': 'Projecting Clauses',
        'writing': 'Writing Clauses',
        'set_operations': 'Set Operations',
        'string': 'String Functions',
        'numeric': 'Numeric Functions',
        'list': 'List Functions',
        'aggregation': 'Aggregation Functions',
        'predicate': 'Predicate Functions',
        'scalar': 'Scalar Functions',
        'temporal': 'Temporal Functions',
        'spatial': 'Spatial Functions',
        'path': 'Path Functions',
        'comparison': 'Comparison Operators',
        'logical': 'Logical Operators',
        'arithmetic': 'Arithmetic Operators',
        'pattern_matching': 'Pattern Matching'
    }

    rel_count = 0
    for feature in all_features:
        feature_node = feature_nodes[feature['name']]
        category_name = category_map.get(feature['subcategory'])

        if category_name and category_name in category_nodes:
            category_node = category_nodes[category_name]
            gf.create_relationship(
                src=feature_node,
                dst=category_node,
                rel_type='BELONGS_TO_CATEGORY'
            )
            rel_count += 1

    print(f"  Created {rel_count} BELONGS_TO_CATEGORY relationships")

    # Commit the transaction
    gf.commit()

    # Print summary statistics
    print("\n" + "="*60)
    print("GRAPH BUILD COMPLETE")
    print("="*60)

    # Query statistics
    print("\nNode Statistics:")
    result = gf.execute("MATCH (n:Feature) RETURN count(n) AS count")
    print(f"  Features: {result[0]['count'].value}")

    result = gf.execute("MATCH (n:Category) RETURN count(n) AS count")
    print(f"  Categories: {result[0]['count'].value}")

    result = gf.execute("MATCH (n:Implementation) RETURN count(n) AS count")
    print(f"  Implementations: {result[0]['count'].value}")

    print("\nRelationship Statistics:")
    result = gf.execute("MATCH ()-[r:IMPLEMENTED_IN]->() RETURN count(r) AS count")
    print(f"  IMPLEMENTED_IN: {result[0]['count'].value}")

    result = gf.execute("MATCH ()-[r:BELONGS_TO_CATEGORY]->() RETURN count(r) AS count")
    print(f"  BELONGS_TO_CATEGORY: {result[0]['count'].value}")

    print("\nImplementation Status:")
    result = gf.execute("""
        MATCH (f:Feature)-[:IMPLEMENTED_IN]->(i:Implementation)
        RETURN i.status AS status, count(f) AS count
        ORDER BY count DESC
    """)
    for row in result:
        print(f"  {row['status'].value}: {row['count'].value}")

    print("\nFeatures by Category:")
    result = gf.execute("""
        MATCH (c:Category)<-[:BELONGS_TO_CATEGORY]-(f:Feature)
        RETURN c.name AS category, count(f) AS count
        ORDER BY count DESC
        LIMIT 10
    """)
    for row in result:
        print(f"  {row['category'].value}: {row['count'].value}")

    print("\n" + "="*60)
    print(f"Graph saved to: {db_path.absolute()}")
    print("="*60)

    return gf


if __name__ == '__main__':
    try:
        build_graph()
        print("\n✅ SUCCESS: Feature graph built successfully!")
        print("   Query it with: GraphForge('docs/feature-graph.db')")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
