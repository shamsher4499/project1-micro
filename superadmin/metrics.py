from prometheus_client import Counter, Gauge, Histogram, Summary

# Define the Prometheus metrics
http_requests_total = Counter('http_requests_total', 'Total number of HTTP requests')
http_request_duration_seconds = Histogram('http_request_duration_seconds', 'HTTP request duration')
database_queries_total = Counter('database_queries_total', 'Total number of database queries')
database_query_duration_seconds = Histogram('database_query_duration_seconds', 'Database query duration')
