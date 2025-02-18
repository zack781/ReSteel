
const { Pool } = require('pg');

const pool = new Pool({
    user: 'raw9846',       
    host: 'localhost',           
    database: 'strucdb',         
    password: 'Resteel123!',  
    port: 5432,                  
});

module.exports = pool;
