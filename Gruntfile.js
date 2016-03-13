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
        },
        copy: {
            development: {
                files: [
                    // includes files within path
                    {expand: false, src: ['./static/js/public.js'], dest: './static/js/public.min.js'}
                ]
            }
        },
        less: {
            development: {
                options: {
                    paths: ["static/less"]
                },
                files: {
                    "static/css/public.min.css": "static/less/public.less"
                }
            },
            prod: {
                options: {
                    paths: ["static/less"],
                    plugins: [
                        new (require('less-plugin-clean-css'))({
                            advanced: true,
                            compatibility: 'ie8'
                        })
                    ]
                },
                files: {
                    "static/css/public.min.css": "static/less/public.less"
                }
            }
        }
    });

    grunt.loadNpmTasks('grunt-contrib-requirejs');
    grunt.loadNpmTasks('grunt-contrib-copy');
    grunt.loadNpmTasks('grunt-contrib-less');

    // Default task(s).
    grunt.registerTask('default', ['copy:development', 'less:development']);
    grunt.registerTask('prod', ['requirejs:compilePublic', 'less:prod']);
};