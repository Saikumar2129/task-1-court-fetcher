DROP TABLE IF EXISTS query_log;

CREATE TABLE query_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  query_params TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('SUCCESS', 'ERROR')),
  response_data TEXT,
  error_message TEXT
);
