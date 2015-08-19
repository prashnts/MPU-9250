
var point = {
    // To Doc.
    init: function (canvas_id) {
        "use strict";
        this.WIDTH = window.innerWidth;
        this.HEIGHT = window.innerHeight;
        this.init_scene();
        this.init_camera();
        this.init_canvas(canvas_id);
        this.init_pc_deps();
        document.addEventListener('mousemove', point.onDocumentMouseMove, false);

    },

    /**
     * Initializes the Perspective Camera object.
     */
    init_camera: function () {
        "use strict";
        var field_of_view = 200,
            aspect_ratio  = this.HEIGHT / this.WIDTH,
            near_plane    = 0.1,
            far_plane     = 1000;

        this.camera = new THREE.PerspectiveCamera(field_of_view, aspect_ratio, near_plane, far_plane);
    },

    // To Doc.
    init_canvas: function (canvas_id) {
        "use strict";
        if (canvas_id) {
            // To do.
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
        "use strict";
        this.scene = new THREE.Scene();
    },

    init_pc_deps: function () {
        this.geometry = new THREE.Geometry();
    },

    render: function () {
        "use strict";
        point.set_camera_position({
            x: point.mouseX,
            y: point.mouseY
        });
        requestAnimationFrame(point.render);
        point.renderer.render(point.scene, point.camera);
        point.camera.lookAt(point.scene.position)
    },

    set_camera_position: function (pos) {
        "use strict";
        if (pos.x) {
            this.camera.position.x += (pos.x - this.camera.position.x) * 0.05;
        }
        if (pos.y) {
            this.camera.position.y += (pos.y - this.camera.position.y) * 0.05;
        }
        if (pos.z) {
            this.camera.position.z = pos.z;
        }
    },

    append_point: function (x, y, z, size, color) {
        var vertex = new THREE.Vector3();

        vertex.x = x;
        vertex.y = y;
        vertex.z = z;

        this.geometry.vertices.push(vertex);

        var material = new THREE.PointCloudMaterial({size: size});
        var particle = new THREE.PointCloud(this.geometry, material);

        return this.scene.add(particle);
    },

    onDocumentMouseMove: function (e) {
        if (e.shiftKey) {
            point.mouseX = e.clientX - point.WIDTH / 2;
            point.mouseY = e.clientY - point.HEIGHT / 2;
        }
    }
};

point.init();
point.set_camera_position({z: -20});



for (var i = 0; i < b.length - 150; i += 1) {
    for (var j = 0; j < b[i].length - 150; j += 1) {
        point.append_point(i, j, b[i][j], 1, 0xffffff);
    }
}

point.render();


