const express = require('express');
const pool = require('../config/db');

const router = express.Router();

// Create (Insert Data)
router.post('/:table', async (req, res) => {
    const { table } = req.params;
    const data = req.body;

    const keys = Object.keys(data).join(', ');
    const values = Object.values(data);
    const placeholders = values.map((_, i) => `$${i + 1}`).join(', ');

    const query = `INSERT INTO ${table} (${keys}) VALUES (${placeholders}) RETURNING *`;

    try {
        const result = await pool.query(query, values);
        res.status(201).json(result.rows[0]);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Read (Get All Data)
router.get('/:table', async (req, res) => {
    const { table } = req.params;
    try {
        const result = await pool.query(`SELECT * FROM ${table}`);
        res.json(result.rows);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Update (Modify Data)
router.put('/:table/:id', async (req, res) => {
    const { table, id } = req.params;
    const updates = req.body;

    const setClause = Object.keys(updates).map((key, i) => `${key} = $${i + 1}`).join(', ');
    const values = Object.values(updates);
    
    const query = `UPDATE ${table} SET ${setClause} WHERE id = $${values.length + 1} RETURNING *`;

    try {
        const result = await pool.query(query, [...values, id]);
        res.json(result.rows[0]);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Delete (Remove Data)
router.delete('/:table/:id', async (req, res) => {
    const { table, id } = req.params;

    try {
        await pool.query(`DELETE FROM ${table} WHERE id = $1`, [id]);
        res.json({ message: 'Deleted successfully' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

module.exports = router;

