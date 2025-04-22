const corelink = require('./corelink.lib.js');
const fs = require('fs');
const { spawn } = require('child_process');

const config = {
  ControlPort: 20012,
  // ControlIP: '127.0.0.1',
  ControlIP: process.env.CORELINK_HOST,
  // ControlIP: '198.22.255.16',
  autoReconnect: false,
  /*
    for service in a local network please replace the certificate with the appropriate version
  cert: '<corelink-tools-repo>/config/ca-crt.pem'
  */
  cert: process.env.CERT_PATH
}

const username = process.env.CORELINK_USERNAME
const password = process.env.CORELINK_PASSWORD

const workspace = 'Holodeck'
const protocol = 'tcp'
const datatype = 'image-capturing'
var arr = [];
var index = 0;

process.on('SIGINT', () => {
  console.log('Disconnect Corelink gracefully...');
  corelink.disconnect();
  process.exit(0);
});

const run = async () => {
  if (await corelink.connect({ username, password }, config).catch((err) => { console.log(err) })) {
    await corelink.createReceiver({
      workspace,
      protocol,
      type: datatype,
      echo: true,
      alert: true,
    }).catch((err) => { console.log(err) })

    corelink.on('receiver', async (data) => {
      const options = { streamIDs: [data.streamID] }
      console.log('on receiver');
      await corelink.subscribe(options)
    })

    corelink.on('data', (streamID, data, header) => {
      // console.log(streamID, data.toString(), JSON.stringify(header))
      // console.log('header = ', header);
      console.log('header[seq-num] = ', header['seq-num']);
      // if (header['seq-num'] === index) {
      //   arr(data);
      //   index+=2048;
      // }
      arr[header['seq-num']] = data;

      if (header['last-chunk']) {
        console.log('last chunk');
        const totalChunks = Object.keys(arr).map(Number).sort((a, b) => a - b);
        const buffers = totalChunks.map(k => {
          const chunk = arr[k];
          if (!chunk) {
            throw new Error(`Missing chunk at sequence ${k}`);
          }
          return chunk;
        });
        const buf = Buffer.concat(buffers);
        // console.log('buf = ', buf);

        if (!fs.existsSync(header['filename'])) {
          fs.writeFile(header['filename'], buf, function(err) {
            if (err) {
              console.error("Error saving image buffer to file:", err);

              // trigger inbound (pass in image path)
              // wait for inbound script to signal complettion
            } else {
              console.log("Image saved as output_from_buffer.jpg");
              // const inboundScript = '../inbound/image_processing.py';
              // const inboundProcess = spawn('python', [inboundScript, 'output_from_buffer.jpg']);

            }
          });
        }

        arr = [];
        index = 0;
      }
    })
  }
}

run()
