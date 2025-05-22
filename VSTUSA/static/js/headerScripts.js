document.addEventListener("DOMContentLoaded", function() {
    const multiple_pillbox_width = "15%";
    const no_results_text = "Ничего не найдено";
    
    $(document).ready(function() {
        $(".date-select").select2({
            placeholder : "Дата",
            allowClear : false,
            width : "100%",
            minimumResultsForSearch : Infinity
        });
    });

    $(document).ready(function() {
        $(".group-pillbox").select2({
            placeholder : "Группа",
            allowClear : true,
            width : multiple_pillbox_width,
            closeOnSelect : false,
            "language": {
                "noResults": function() { return no_results_text; }
            },
            escapeMarkup: function (markup) { return markup; }
        });
    });

    $(document).ready(function() {
        $(".teacher-pillbox").select2({
            placeholder : "Преподаватель",
            allowClear : true,
            width : multiple_pillbox_width,
            closeOnSelect : false,
            "language": {
                "noResults": function() { return no_results_text; }
            },
            escapeMarkup: function (markup) { return markup; }
        });
    });

    $(document).ready(function() {
        $(".place-pillbox").select2({
            placeholder : "Аудитория",
            allowClear : true,
            width : multiple_pillbox_width,
            closeOnSelect : false,
            "language": {
                "noResults": function() { return no_results_text; }
            },
            escapeMarkup: function (markup) { return markup; }
        });
    });

    $(document).ready(function() {
        $(".subject-pillbox").select2({
            placeholder : "Предмет",
            allowClear : true,
            width : multiple_pillbox_width,
            closeOnSelect : false,
            "language": {
                "noResults": function() { return no_results_text; }
            },
            escapeMarkup: function (markup) { return markup; }
        });
    });

    $(document).ready(function() {
        $(".kind-pillbox").select2({
            placeholder : "Тип предмета",
            allowClear : true,
            width : multiple_pillbox_width,
            closeOnSelect : false,
            "language": {
                "noResults": function() { return no_results_text; }
            },
            escapeMarkup: function (markup) { return markup; }
        });
    });

    $(document).ready(function() {
        $(".time-slot-pillbox").select2({
            placeholder : "Время проведения",
            allowClear : true,
            width : multiple_pillbox_width,
            closeOnSelect : false,
            "language": {
                "noResults": function() { return no_results_text; }
            },
            escapeMarkup: function (markup) { return markup; }
        });
    });
});

document.onkeydown = function(e) {
    if (e.key === "Enter") {
        document.getElementById("header-form").submit();
    }
    else if (e.key === "Backspace") {
        drop_filters();
    }
};

function on_date_select_change() {
    var selected_value = document.getElementById("date-select").value;

    if (selected_value != "single_date" && selected_value != "range_date") {
        document.getElementById("specified-date-container").style.display = "none";
        document.getElementById("left-date").display = "none";
        document.getElementById("right-date").display = "none";
    }
    else {
        document.getElementById("specified-date-container").style.display = "flex";
        document.getElementById("left-date").style.display = "inline";

        if (selected_value == "range_date")
            document.getElementById("right-date").style.display = "inline";
        else
            document.getElementById("right-date").style.display = "none";
    }
}

function update_filters_visibility() {
    var container = document.getElementById("addition-filters-container");
    
    if (container.style.display == "none") {
        container.style.display = "flex";
        document.getElementById("more-filters-button").innerText = "Меньше фильтров";
        document.getElementById("filters-visibility-state").value = "1";
    }
    else {
        container.style.display = "none";
        document.getElementById("more-filters-button").innerText = "Больше фильтров";
        document.getElementById("filters-visibility-state").value = "0";
    }
}

function drop_filters() {
    $("select").not(".date-select").each(function() {
        if ($(this).data("select2")) 
            $(this).val([]).trigger("change");
    });

    $(".date-select").val("today").trigger("change");

    document.getElementById("left-date").value = "none";
    document.getElementById("right-date").value = "none";
}