-- Create test database (run automatically by docker-entrypoint-initdb.d)
CREATE DATABASE tendercheck_test;
GRANT ALL PRIVILEGES ON DATABASE tendercheck_test TO tendercheck;
