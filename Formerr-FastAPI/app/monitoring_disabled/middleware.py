# app/monitoring/middleware.py - DATABASE METRICS MIDDLEWARE
import time
from typing import Callable
from sqlalchemy import event
from sqlalchemy.engine import Engine
from app.monitoring.prometheus_service import prometheus_metrics


class DatabaseMetricsMiddleware:
    """Middleware para trackear queries do database"""

    @staticmethod
    def setup_database_monitoring():
        """Setup database event listeners"""

        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
            context._query_statement = statement

        @event.listens_for(Engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            duration = time.time() - context._query_start_time

            # Extract table name and operation
            statement_lower = statement.lower().strip()

            # Determine operation
            if statement_lower.startswith('select'):
                operation = 'select'
            elif statement_lower.startswith('insert'):
                operation = 'insert'
            elif statement_lower.startswith('update'):
                operation = 'update'
            elif statement_lower.startswith('delete'):
                operation = 'delete'
            else:
                operation = 'other'

            # Extract table name (simplified)
            table = "unknown"
            try:
                if 'from ' in statement_lower:
                    table_part = statement_lower.split('from ')[1].split(' ')[0]
                    table = table_part.strip('`"[]')
                elif 'into ' in statement_lower:
                    table_part = statement_lower.split('into ')[1].split(' ')[0]
                    table = table_part.strip('`"[]')
                elif 'update ' in statement_lower:
                    table_part = statement_lower.split('update ')[1].split(' ')[0]
                    table = table_part.strip('`"[]')
            except:
                table = "unknown"

            # Track metric
            prometheus_metrics.observe_database_query(table, operation, duration)