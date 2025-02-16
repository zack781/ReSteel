const corelink = require('corelink-client');
const fs = require('fs');

const config = {
  ControlPort: 20012,
  ControlIP: '127.0.0.1',
  // ControlIP: process.env.CORELINK_HOST,
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
      await corelink.subscribe(options)
    })

    corelink.on('data', (streamID, data, header) => {
      // console.log(streamID, data.toString(), JSON.stringify(header))
      console.log('data = ', data);
      console.log('header = ', header);
      if (header['seq-num'] === index) {
        arr.push(data);
        index+=1024;
      }
      if (header['last-chunk']) {
        const buf = Buffer.concat(arr);
        console.log('buf = ', buf);

        fs.writeFile("output_from_buffer.jpg", buf, function(err) {
          if (err) {
            console.error("Error saving image buffer to file:", err);
          } else {
            console.log("Image saved as output_from_buffer.jpg");
          }
        });

        arr = [];
        index = 0;
      }
    })
  }
}

run()
