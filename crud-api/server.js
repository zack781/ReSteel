const express = require('express');
const cors = require('cors');
const pool = require('./config/db'); // Import database config
const dynamicRoutes = require('./routes/dynamicRoutes'); // Import dynamic CRUD routes

const app = express();
const port = 3000;

app.use(express.json()); // Middleware to parse JSON
app.use(cors()); // Enable CORS for API access from different origins

//Test Database Connection
pool.query('SELECT NOW()', (err, res) => {
    if (err) {
        console.error('Database connection error:', err);
    } else {
        console.log('Connected to the database at', res.rows[0].now);
    }
});

// Root API test route
app.get('/', (req, res) => {
    res.send('API is running!');
});

// Load Dynamic CRUD API Routes
app.use('/api', dynamicRoutes);

// Start the server
app.listen(port, () => {
    console.log(`Server running on http://localhost:${port}`);
});

