document.addEventListener("DOMContentLoaded", function() {
    $(document).ready(function() {
        $(".date-select").select2({
            placeholder : "Дата",
            allowClear : false
        });
    });

    $(document).ready(function() {
        $(".group-pillbox").select2({
            placeholder : "Группа",
            allowClear : true,
            closeOnSelect : false
        });
    });

    $(document).ready(function() {
        $(".teacher-pillbox").select2({
            placeholder : "Преподаватель",
            allowClear : true,
            closeOnSelect : false
        });
    });

    $(document).ready(function() {
        $(".place-pillbox").select2({
            placeholder : "Аудитория",
            allowClear : true,
            closeOnSelect : false
        });
    });

    $(document).ready(function() {
        $(".subject-pillbox").select2({
            placeholder : "Предмет",
            allowClear : true,
            closeOnSelect : false
        });
    });

    $(document).ready(function() {
        $(".time-slot-pillbox").select2({
            placeholder : "Время проведения",
            allowClear : true,
            closeOnSelect : false
        });
    });
});

function update_filters_visibility() {
    var container = document.getElementById("filters-container")
    
    if (container.style.display == "none") {
        container.style.display = "block";
        document.getElementById("filters-button").innerText = "Меньше фильтров";
        document.getElementById("filters-visibility-state").value = "1";
    }
    else {
        container.style.display = "none";
        document.getElementById("filters-button").innerText = "Больше фильтров";
        document.getElementById("filters-visibility-state").value = "0";
    }
}

function drop_filters() {
    $("select").not(".date-select").each(function() {
        if ($(this).data("select2")) 
            $(this).val([]).trigger("change");
    });

    $(".date-select").val("today").trigger("change");
}