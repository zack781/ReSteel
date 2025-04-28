# ReSteel CRUD API

This project is a CRUD API that interacts with a PostgreSQL database to manage materials, including images and optimized areas.

## Getting Started

### Prerequisites
- Node.js
- PostgreSQL

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/ReSteel.git
   
2. Navitgate to the project directory
3. copy the .env.example to .env file and modify the variables as need
4. Run the setup script to initialize the dataabase
   ./setup.sh #for linux 
   setup.bat #for windows
5. Isntall dependencies
   npm install 
6. Start the server 
   npm start
 
 7. After setting up the database instance then we can use these curl commands to test: 
# For posting the boards data
 curl -X POST http://localhost:3000/api/boards/full \
  -H "Content-Type: application/json" \
  -d '{
    "png_path": "IMG-5284.jpg",
    "dxf_raw_path": "intermediate.dxf",
    "dxf_processed_path": "result.dxf",
    "length": 300,
    "width": 150,
    "measurements": [
      { "rectangles": [[120,0,0,0]], "length": 120, "width": 80 },
      { "rectangles": [[180,5,5,5]], "length": 180, "width": 90 }
    ]
  }'
  
# For Getting the best measurements
 curl "http://localhost:3000/api/measurements/best?length=100&width=50"
