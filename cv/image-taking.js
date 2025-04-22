const corelink = require('./corelink.lib.js')

const config = {
  ControlPort: 20012,
  // ControlIP: '127.0.0.1',
  ControlIP: process.env.CORELINK_HOST,

  /*
  autoReconnect: false,
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

process.on('SIGINT', () => {
  console.log('Disconnect Corelink gracefully...');
  corelink.disconnect();
  process.exit(0);
});

process.on('SIGTSTP', () => {
  console.log('Disconnect Corelink gracefully...');
  corelink.disconnect();
  process.exit(0);
});

const fs = require('fs');
const { spawn } = require('child_process');

let imgCount = 0;
const run = async () => {
    // corelink.setDebug(true);
    if (await corelink.connect({ username, password }, config).catch((err) => { console.log(err) })) {
    let sender = await corelink.createSender({
      workspace,
      protocol,
      type: datatype,
      metadata: { name: 'image-capturing' },
    }).catch((err) => { console.log(err) })

    corelink.on('sender', (data) => {
      console.log("sender = ", data);

      async function loop() {
        while (true) {
          // your logic here (preferably non-blocking)
          const filePath = './test' + imgCount + '.jpg';
          if (fs.existsSync(filePath)) {
            console.log('Sending image...');
            const imgBuff = fs.readFileSync(filePath);
            const buffer = Buffer.from(imgBuff);
            console.log('Buffer length:', buffer.length);
            const bufferLength = buffer.length;

            let counter = 0;

            async function sendChunk() {
              while (counter < bufferLength) {
                const chunk = counter + 1024 < bufferLength ? buffer.slice(counter, counter + 1024) : buffer.slice(counter, bufferLength);
                const lastChunk = counter + 1024 >= bufferLength;
                console.log('Sending chunk:', counter, 'Last chunk:', lastChunk);
                corelink.send(sender, chunk, { "seq-num": counter, "last-chunk": lastChunk, "filename": filePath, "file-size": bufferLength });
                counter += 1024;

                await new Promise(resolve => setTimeout(resolve, 10)); // simulate async wait
              }
            }

            sendChunk();
            imgCount++;
          }
          await new Promise(resolve => setTimeout(resolve, 100)); // simulate async wait
        }
        console.log('Exited loop');
      }

      loop();
    })

  }
}

run()


