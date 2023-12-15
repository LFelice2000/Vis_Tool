/**
 * Fichero que controla la visualización de las gráficas de progreso
 */

global_url = 'https://jljorro.github.io/SOPER-vis/data/global.json';
students_url = 'https://jljorro.github.io/SOPER-vis/data/students.json';

function getUrlParameter(name) {
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
    results = regex.exec(location.search);
    return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}

$(document).ready(function () {

    studentName = getUrlParameter('student');

    $.getJSON(global_url, function (global_data) {
        global_data.global.forEach(function (element) {
            $('#' + element.id).animate({
                width: element.value + '%'
            }, 1000);

            $('#' + element.id).text(element.value + '%');
        });

        $('#actualizacion').text("Actualizado: " + global_data.actualizacion);
    });

    $.getJSON(students_url, function (student_data) {
        
        student = null;
        for(std in student_data.students) {
            if (student_data.students[std].username === studentName) {
                student = student_data.students[std];
                break;
            }
        }

        if (student === null) {
            alert('No existe el estudiante');
            return;
        } else {
            $('#student-progress-vis').show();

            student.progress.forEach(function (element) {
                $('#' + element.id).animate({
                    width: element.value + '%'
                }, 1000);

                $('#' + element.id).text(element.value + '%');
            });
        }

    });
   /* data.global.forEach(function (element) {
        $('#' + element.id).animate({
            width: element.value + '%'
        }, 1000);
    });*/

   /*$('#mostrar-btn').click(function (event) {
        event.preventDefault();

        studentName = $('#student-name-txt').val();

        $.getJSON(students_url, function (student_data) {
            // Busco al estudiante
            student = null;
            for(std in student_data.students) {
                if (student_data.students[std].username === studentName) {
                    student = student_data.students[std];
                    break;
                }
            }

            if (student === null) {
                alert('No existe el estudiante');
                return;
            } else {
                $('#student-progress-vis').show();
    
                student.progress.forEach(function (element) {
                    $('#' + element.id).animate({
                        width: element.value + '%'
                    }, 1000);
                });
            }

        });

    });*/
   

});