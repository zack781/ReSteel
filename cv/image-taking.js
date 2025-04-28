const corelink = require('./corelink.lib.js')
const sharp = require('sharp');

const config = {
  ControlPort: 20012,
  // ControlIP: '127.0.0.1',
  ControlIP: process.env.CORELINK_HOST,
  // ControlIP: '128.110.217.55',

  /*
  autoReconnect: false,
    for service in a local network please replace the certificate with the appropriate version
  cert: '<corelink-tools-repo>/config/ca-crt.pem'
  */
  // cert: '/Users/zack/git_repos/ReSteel/ca-crt.pem'
  cert: process.env.CERT_PATH
}

const username = process.env.CORELINK_USERNAME
const password = process.env.CORELINK_PASSWORD

const workspace = 'Holodeck'
const protocol = 'tcp'
const datatype = 'image-capturing'



const fs = require('fs');
const { spawn } = require('child_process');

let imgCount = 0;
let startLoop = false;
let sender =null;

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
    sender = await corelink.createSender({
      workspace,
      protocol,
      type: datatype,
      metadata: { name: 'image-capturing' },
    }).catch((err) => { console.log(err) })

    corelink.on('sender', (data) => {
      console.log("sender = ", data);
      startLoop = true;

    })

  }
}

run()

async function loop() {
  setInterval(async () => {
    if (startLoop) {
      const filePath = './test' + imgCount + '.jpg';
      const outputPath = './output' + imgCount + '.jpg';
      if (fs.existsSync(filePath)) {
        if (!fs.existsSync(outputPath)) {
          sharp(filePath)
          .jpeg({ quality: 100 })           // Compress JPEG (quality 0-100)
          .toFile(outputPath)            // Save compressed image
          .then(() => {
            console.log('Image compressed and saved!');
          })
          .catch(err => {
            console.error('Compression failed:', err);
          });
          await new Promise(resolve => setTimeout(resolve, 1000));
        }

        console.log('Sending image...');
        const imgBuff = fs.readFileSync(outputPath);
        const buffer = Buffer.from(imgBuff);
        console.log('Buffer length:', buffer.length);
        const bufferLength = buffer.length;

        let counter = 0;
        let index = 0;

        async function sendChunk() {
          while (counter < bufferLength) {
            startLoop = false;
            console.log('Sending chunk:', counter);
            const chunk = counter + 1024 < bufferLength ? buffer.slice(counter, counter + 1024) : buffer.slice(counter, bufferLength);
            const lastChunk = counter + 1024 >= bufferLength;
            corelink.send(sender, chunk, { "seq-num": counter, "last-chunk": lastChunk, "filename": outputPath, "file-size": bufferLength, "index": index });

            await new Promise(resolve => setTimeout(resolve, 150));

            counter += 1024;
            index+=1;
          }
          startLoop = true;
        }

        await sendChunk();
        imgCount++;
      }
    }
  }, 100); // every 100 ms check
}

loop()
