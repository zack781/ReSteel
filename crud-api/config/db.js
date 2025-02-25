
const { Pool } = require('pg');
require('dotenv').config();

console.log('username = ', process.env.DB_USER);

const pool = new Pool({
    user: process.env.DB_USER,       // Database user from .env file
    host: process.env.DB_HOST || 'localhost',  // Host for database (use .env or default to localhost)
    database: process.env.DB_NAME || 'strucdb',  // Database name from .env or default to 'strucdb'
    password: process.env.DB_PASSWORD,  // Database password from .env file
    port: process.env.DB_PORT || 5432,  // Port for PostgreSQL (use .env or default to 5432)
});

module.exports = pool;
