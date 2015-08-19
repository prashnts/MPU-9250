var scene = new THREE.Scene();
var camera = new THREE.PerspectiveCamera( 750, window.innerWidth / window.innerHeight, 0.1, 1000 );

var renderer = new THREE.WebGLRenderer();
renderer.setSize( window.innerWidth, window.innerHeight );
document.body.appendChild( renderer.domElement );

var geometry = new THREE.BoxGeometry( 1, 1, 1 );
var material = new THREE.MeshBasicMaterial( { color: 0x00ff00 } );
var cube = new THREE.Mesh( geometry, material );
scene.add( cube );

camera.position.z = 5;

function render() {
    requestAnimationFrame( render );

    renderer.render( scene, camera );
}
render();

var point = {
    init: function (canvas_id) {
        this.WIDTH = window.innerWidth;
        this.HEIGHT = window.innerHeight;
        this.init_scene();
        this.init_camera();
        this.init_canvas();
    },

    /**
     * Initializes the Perspective Camera object.
     */
    init_camera: function () {
        var field_of_view = 20,
            aspect_ratio  = this.HEIGHT / this.WIDTH,
            near_plane    = 1,
            far_plane     = 1000;

        this.camera = new THREE.PerspectiveCamera(field_of_view, aspect_ratio, near_plane, far_plane);
    },

    init_canvas: function (canvas_id) {
        if (canvas_id) {
            //
        }
        else {
            this.renderer = new THREE.WebGLRenderer();
            this.renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(this.renderer.domElement);
        }
    },

    /**
     * Initializes the Scene Object.
     */
    init_scene: function () {
        this.scene = new THREE.Scene();
    }
};