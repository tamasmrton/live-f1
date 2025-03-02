from pathlib import Path


class QueryRegistry:
    def __init__(self):
        self.queries: dict = {}
        self.fetch_queries()

    def fetch_queries(self):
        """Fetch all .sql files and store their content in the queries dictionary."""
        queries_path = Path(__file__).parent / "queries"
        for sql_file in queries_path.glob("*.sql"):
            with sql_file.open("r") as file:
                file_content = file.read()
                query_name = sql_file.name.replace(".sql", "")
                self.queries[query_name] = file_content

    def get_query(self, query_name):
        """Get the content of a specific query by file name."""
        return self.queries.get(query_name, None)

    def list_queries(self):
        """List all available queries."""
        return list(self.queries.keys())
