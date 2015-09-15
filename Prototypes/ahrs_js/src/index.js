var scene, camera, renderer;
var WIDTH  = window.innerWidth;
var HEIGHT = window.innerHeight;
var SPEED = 0.01;
function init() {
    scene = new THREE.Scene();
    initCube();
    initCamera();
    initRenderer();
    document.body.appendChild(renderer.domElement);
}
function initCamera() {
    camera = new THREE.PerspectiveCamera(70, WIDTH / HEIGHT, 1, 10);
    camera.position.set(0, 0, 7);
    camera.lookAt(scene.position);
}
function initRenderer() {
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(WIDTH, HEIGHT);
}
function initCube() {
    cube = new THREE.Mesh(new THREE.CubeGeometry(2, 2, 2), new THREE.MeshNormalMaterial());
    scene.add(cube);
}
function render() {
    requestAnimationFrame(render);
    renderer.render(scene, camera);
}
var angle = 0;
init();
render();
//////////////////////////////////////////////////
// var socket = io('http://localhost:4545');
// socket.on('data', function(data){
//   //var dataArray = data.data.split("\t");
//   console.log(data);
//   //rotateCube(Number(dataArray[1]), Number(dataArray[2]), Number(dataArray[3]));
// });
function rotateCube(yaw, pitch, roll) {
    cube.rotation.z = roll ;//+ (Math.PI);// * (Math.PI/180);
    cube.rotation.x = pitch - Math.PI/2;// + (Math.PI);// * (Math.PI/180);
    cube.rotation.y = yaw;// + (Math.PI);// * (Math.PI/180);
}

var URL = "http://localhost:8086/query?q=SELECT+last(yaw)%2C+last(pitch)%2C+last(roll)+FROM+ahrs+WHERE+mmt_class+%3D+%27random%27&db=imu_data";

window.setInterval(function () {
  $.getJSON(URL, function (data) {
    dat = data.results[0].series[0].values[0];
    console.log(dat);
    //dat = [0, 0, 0, 0]
    rotateCube(dat[1], dat[2], dat[3]);
  });
}, 10);

