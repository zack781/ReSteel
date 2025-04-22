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

// A merged post request

router.post('/boards/full', async (req, res) => {
  const {
    png_path,
    dxf_raw_path,
    dxf_processed_path,
    length: boardLength,
    width: boardWidth,
    measurements
  } = req.body;

  // Basic validation
  if (!png_path || !dxf_raw_path || !dxf_processed_path ||
      boardLength == null || boardWidth == null ||
      !Array.isArray(measurements)) {
    return res.status(400).json({ error: 'Required board fields and measurements[] array.' });
  }

  const client = await pool.connect();
  try {
    await client.query('BEGIN');

    // 1) Insert the board
    const boardInsert = `
      INSERT INTO boards
        (png_path, dxf_raw_path, dxf_processed_path, length, width)
      VALUES ($1, $2, $3, $4, $5)
      RETURNING id, png_path, dxf_processed_path
    `;
    const boardRes = await client.query(boardInsert, [
      png_path, dxf_raw_path, dxf_processed_path, boardLength, boardWidth
    ]);
    const newBoard = boardRes.rows[0];
    const boardId = newBoard.id;

    // 2) Insert each measurement for that board
    const measInsert = `
      INSERT INTO measurements
        (board_id, rectangles, length, width)
      VALUES ($1, $2, $3, $4)
    `;
    for (const m of measurements) {
      // you might want to validate m.rectangles, m.length, m.width here
      await client.query(measInsert, [
        boardId,
        m.rectangles,
        m.length,
        m.width
      ]);
    }

    await client.query('COMMIT');

    // 3) Return the new board and count of measurements inserted
    res.status(201).json({
      board: newBoard,
      measurementsInserted: measurements.length
    });
  } catch (err) {
    await client.query('ROLLBACK');
    console.error(err);
    res.status(500).json({ error: err.message });
  } finally {
    client.release();
  }
});



// GET /measurements/best?length=XX&width=YY[&board_id=ZZ]
router.get('/measurements/best', async (req, res) => {
  try {
    // Parse & validate query parameters
    const reqLength = parseFloat(req.query.length);
    const reqWidth  = parseFloat(req.query.width);
    if (isNaN(reqLength) || isNaN(reqWidth)) {
      return res.status(400).json({ error: 'length and width must be numbers' });
    }

    // Build base SQL
    let sql = `
      SELECT
        m.*,
        b.png_path,
        b.dxf_processed_path,
        (m.length * m.width) AS area
      FROM measurements m
      JOIN boards b ON m.board_id = b.id
      WHERE m.length >= $1
        AND m.width  >= $2
    `;
    const params = [reqLength, reqWidth];

    // (optional) filter by board_id if provided
    if (req.query.board_id) {
      sql += ` AND m.board_id = $3`;
      params.push(parseInt(req.query.board_id, 10));
    }

    // order by smallest area first, pick 1
    sql += ` ORDER BY area ASC LIMIT 1`;

    //  execute query
    const { rows } = await pool.query(sql, params);
    if (rows.length === 0) {
      return res.status(404).json({ message: 'No rectangle meets those dimensions.' });
    }

    // respond with the best-fit rectangle
    res.json(rows[0]);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});


module.exports = router;

