const corelink = require('./corelink.lib.js');
const fs = require('fs');
const { spawn } = require('child_process');
require('dotenv').config();
const https = require('https');


const config = {
  ControlPort: 20012,
  ControlIP: process.env.CORELINK_HOST,
  autoReconnect: false,
  /*
    for service in a local network please replace the certificate with the appropriate version
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
let receiver = null;

process.on('SIGINT', () => {
  console.log('Disconnect Corelink gracefully...');
  corelink.disconnect({workspaces: [workspace], types: [datatype]});
  process.exit(0);
});

process.on('SIGTSTP', () => {
  console.log('Disconnect Corelink gracefully...');
  corelink.disconnect({workspaces: [workspace], types: [datatype]});

  process.exit(0);
});

const inboundScript = '../inbound/image_processing.py';
spawn('bash', ['-c', 'source ./venv/bin/activate']);
spawn('pip3', ['install', '-r', 'requirements.txt']);

const run = async () => {
  corelink.setDebug(true);
  if (await corelink.connect({ username, password }, config).catch((err) => { console.log(err) })) {
    receiver = await corelink.createReceiver({
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
      console.log('seq-num, index = ', header['seq-num'], ' - ', index);
      arr[header['index']] = data;
      index+=1024;


      if (header['last-chunk']) {

        console.log('arr = ', arr);
        // console.log('last chunk');
        // arr = arr.map((chunk, i) => {
        //   if (!chunk) {
        //     return Buffer.alloc(1024);
        //   } else {
        //     return chunk;
        //   }
        // });
        for (let i = 0; i < Math.ceil(header['file-size'] / 1024); i++) {
          if (arr[i] === undefined) {
            arr[i] = Buffer.alloc(1024);
          }
        }
        // const totalChunks = Object.keys(arr).map(Number).sort((a, b) => a - b);
        // console.log('totalChunks = ', totalChunks);
        // const buffers = totalChunks.map(k => {
        //   const chunk = arr[k];
        //   if (!chunk) {
        //     console.log('chunk is empty');
        //     return Buffer.alloc(1024);
        //   }
        //   return chunk;
        // });

        // console.log('buffers = ', buffers);

        console.log('arr = ', arr);
        const buf = Buffer.concat(arr);
        // console.log('buf = ', buf);
        console.log(buf.size);

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
              const filename = header['filename'].replace('.jpg', '');
              inboundProcess = spawn('python3', [inboundScript, header['filename'], filename + '_intermediate.dxf', filename + '_intermediate_scaled.dxf', filename + '_final_output.dxf']);

              inboundProcess.stdout.on('data', (data) => {
                console.log(`stdout: ${data}`);
                if (data.toString().includes('record')) {
                  const str = data.toString();
                  const matches = [...str.matchAll(/record=\s*(\[\(.*?\)\])/g)];

                  const rectanglesArray = matches.map(match => {
                    const raw = match[1]
                      .replace(/\(/g, '[')
                      .replace(/\)/g, ']');

                    const parsed = JSON.parse(raw); // will be an array of arrays

                    return parsed.map(([x, y, length, width]) => ({
                      rectangles: [[x, y, 0, 0]],
                      length,
                      width
                    }));
                  }).flat(); // flatten in case multiple rects per line

                  console.log(rectanglesArray);
                }
                if (data.toString().includes('COMPLETED')) {
                  console.log('inbound script completed');

                  // const data = JSON.stringify({
                  //   {
                  //     "png_path": header['filename'],
                  //     "dxf_raw_path": filename + '_intermediate.dxf',
                  //     "dxf_processed_path": filename + '_intermediate_scaled.dxf',
                  //     "length": 0,
                  //     "width": 0,
                  //     "measurements": [
                  //       { "rectangles": [[120,0,0,0]], "length": 120, "width": 80 },
                  //       { "rectangles": [[180,5,5,5]], "length": 180, "width": 90 }
                  //     ]
                  //   }
                  // });

                  // const options = {
                  //   hostname: 'api.example.com',
                  //   path: '/submit',
                  //   method: 'POST',
                  //   headers: {
                  //     'Content-Type': 'application/json',
                  //     'Content-Length': data.length
                  //   }
                  // };
                }
              });
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
