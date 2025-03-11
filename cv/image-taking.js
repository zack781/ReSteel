const corelink = require('./corelink.lib.js')

const config = {
  ControlPort: 20012,
  ControlIP: '127.0.0.1',
  // ControlIP: 'corelink.hsrn.nyu.edu',

  /*
  autoReconnect: false,
    for service in a local network please replace the certificate with the appropriate version
  cert: '<corelink-tools-repo>/config/ca-crt.pem'
  */
  cert: '/Users/zack/Documents/repos/corelink-server/config/ca-crt.pem'
}

const username = 'Testuser'
const password = 'Testpassword'

const workspace = 'Holodeck'
const protocol = 'tcp'
const datatype = 'image-capturing'

process.on('SIGINT', () => {
  console.log('Disconnect Corelink gracefully...');
  corelink.disconnect();
  process.exit(0);
});

var NodeWebcam = require( "node-webcam" );
const fs = require('fs');
const { spawn } = require('child_process');

const imgTriggerScript = './img-trigger.py';

spawn('bash', ['-c', 'source ./venv/bin/activate']);
spawn('pip', ['install', '-r', 'requirements.txt']);

const pythonProcess = spawn('python', [imgTriggerScript]);

pythonProcess.stdout.on('data', (data) => {
  const output = data.toString();
  console.log('Python script output:', output);
});

var opts = {
  width: 100,
  height: 70,
  quality: 20,

  // Number of frames to capture
  // More the frames, longer it takes to capture
  // Use higher framerate for quality. Ex: 60
  frames: 30,

  //Delay in seconds to take shot
  //if the platform supports miliseconds
  //use a float (0.1)
  //Currently only on windows
  delay: 0,

  //Save shots in memory
  saveShots: true,


  output: "jpeg",
  device: false,
  // Set callbackReturn to "buffer" so that the callback receives a Buffer instead of a file path
  callbackReturn: "buffer",
  verbose: false
};


//Creates webcam instance

var Webcam = NodeWebcam.create( opts );

let imgBuff;

Webcam.capture("buffer_example", function(err, imageBuffer) {
  if (err) {
    console.error("Error capturing image:", err);
    return;
  }

  // `imageBuffer` is a Buffer containing the JPEG image data
  console.log("Image captured as a buffer. Buffer size:", imageBuffer.length);
  imgBuff = imageBuffer;

  // Optionally, write the buffer to a file manually
  fs.writeFile("output_from_buffer.jpg", imageBuffer, function(err) {
    if (err) {
      console.error("Error saving image buffer to file:", err);
    } else {
      console.log("Image saved as output_from_buffer.jpg");
      run();
    }
  });
});


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
      let counter = 0;
      console.log('imgBuff = ', imgBuff);
      const buffer = Buffer.from(imgBuff);
      const bufferLength = buffer.length;

      console.log("bufferLength = ", bufferLength);

      async function sendChunk() {

      while (counter < bufferLength) {
        console.log('bufferLength = ', bufferLength);
        console.log('counter = ', counter);
        const chunk = counter + 1024 < bufferLength ? buffer.slice(counter, counter + 1024) : buffer.slice(counter, bufferLength);
        const lastChunk = counter + 1024 >= bufferLength;
        corelink.send(sender, chunk, { "seq-num": counter, "last-chunk": lastChunk});
        counter += 1024;
        await new Promise(r => setTimeout(r, 100));
      }
      }

      sendChunk();

      // corelink.send(sender, buffer, { "seq-num": counter});
    })
  }
}
