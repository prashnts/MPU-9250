module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    concat: {
      options: {
        separator: ';',
      },
      dist: {
        src: [
          "bower_components/jquery/dist/jquery.js",
          "bower_components/three.js/three.min.js",
          "src/index.js"
        ],
        dest: 'dist/built.js',
      },
    },
    watch: {
      scripts: {
        files: ["src/index.js"],
        tasks: ['concat'],
        options: {
          spawn: false,
        },
      },
    },
  });

  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-sass');
  grunt.loadNpmTasks('grunt-contrib-watch');

  // Default task(s).
  grunt.registerTask('default', ['watch']);

};
