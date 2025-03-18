#!/bin/bash

echo "Setting up the PostgreSQL database..."

# Load environment variables
source ./config/.env

# Run the SQL script to initialize the database
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -f ./crud-api/init.sql

echo "Database setup complete!"
