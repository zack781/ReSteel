CREATE DATABASE strucdb;  // creating a new database

\c strucdb;



CREATE TABLE boards (
    id SERIAL PRIMARY KEY,
    png_path TEXT NOT NULL,
    dxf_raw_path TEXT NOT NULL,
    dxf_processed_path TEXT NOT NULL,
    length FLOAT NOT NULL,
    width FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
 
CREATE TABLE measurements (
    id SERIAL PRIMARY KEY,
    board_id INT REFERENCES boards(id) ON DELETE CASCADE,
    rectangles FLOAT[][4],  -- Each rectangle has 4 values: (w, x, y, z)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
