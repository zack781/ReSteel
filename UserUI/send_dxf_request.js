const corelink = require('corelink-client');
const fs = require('fs');

// ⛳ Adjust this if needed to point to your actual .pem cert
const config = {
  ControlPort: 20012,
  ControlIP: '127.0.0.1',
  autoReconnect: false,
  cert: '/Users/chriswan/Desktop/certs/ca-crt.pem' // <- change this if you got a new cert
};

const username = process.env.CORELINK_USERNAME;
const password = process.env.CORELINK_PASSWORD;

const workspace = 'Holodeck';
const protocol = 'tcp';
const datatype = 'dxf-request'; // 🔁 you can name it whatever is expected on the receiver side

// ⬇️ Load the DXF object (created by Flask) from dxf_request.json
let requestJSON = {};
try {
  const jsonPath = process.argv[2];
  if (!jsonPath || !fs.existsSync(jsonPath)) {
    throw new Error("Missing or invalid path to DXF request file.");
  }
  const fileData = fs.readFileSync(jsonPath);
  requestJSON = JSON.parse(fileData);
} catch (err) {
  console.error("❌ Failed to read DXF request:", err.message);
  process.exit(1);
}

const run = async () => {
  if (await corelink.connect({ username, password }, config).catch((err) => { console.log("❌ Connection error:", err); })) {

    // Create a sender just like in the webcam code
    await corelink.createSender({
      workspace,
      protocol,
      type: datatype,
      echo: true,
      alert: true,
    }).catch((err) => { console.log("❌ Sender creation error:", err); });

    // When the sender is ready, send the DXF object
    corelink.on('sender', async (data) => {
      const streamID = data.streamID;

      const messageBuffer = Buffer.from(JSON.stringify(requestJSON));
      const totalLength = messageBuffer.length;
      let index = 0;
      let chunkSize = 1024;

      console.log("📦 Sending DXF request in chunks...");

      while (index < totalLength) {
        const isLast = index + chunkSize >= totalLength;
        const chunk = isLast
          ? messageBuffer.slice(index)
          : messageBuffer.slice(index, index + chunkSize);

        corelink.send({ streamID }, chunk, {
          'seq-num': index,
          'last-chunk': isLast
        });

        index += chunkSize;
        await new Promise((r) => setTimeout(r, 50)); // optional pacing
      }

      console.log("✅ DXF request sent via CoreLink.");
    });
  }
};

run();
