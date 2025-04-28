const corelink = require('./corelink.lib.js');
const fs = require('fs');
const { spawn } = require('child_process');

const config = {
  ControlPort: 20012,
  // ControlIP: '127.0.0.1',
  ControlIP: process.env.CORELINK_HOST,
  // ControlIP: '128.110.217.55',
  autoReconnect: false,
  /*
    for service in a local network please replace the certificate with the appropriate version
  cert: '<corelink-tools-repo>/config/ca-crt.pem'
  */
  cert: process.env.CERT_PATH
  // cert: '/Users/zack/git_repos/ReSteel/ca-crt.pem'
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
      // console.log(streamID, data.toString(), JSON.stringify(header))
      // console.log('header = ', header);
      // console.log('header[seq-num] = ', header['seq-num']);
      // console.log('data = ', data);
      // if (header['seq-num'] === index) {
      //   arr(data);
      //   index+=2048;
      // }
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
