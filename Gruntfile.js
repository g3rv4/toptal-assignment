module.exports = function (grunt) {

    // Project configuration.
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        requirejs: {
            compilePublic: {
                options: {
                    optimize: "uglify2",
                    preserveLicenseComments: false,
                    generateSourceMaps: true,
                    skipDirOptimize: false,

                    baseUrl: './static/js',
                    mainConfigFile: './static/js/require/config.js',
                    name: "public",
                    include: ['apps/public'],
                    out: "static/js/public.min.js"
                }
            }
        }
    });

    grunt.loadNpmTasks('grunt-contrib-requirejs');

    // Default task(s).
    grunt.registerTask('default', ['requirejs:compilePublic']);
};