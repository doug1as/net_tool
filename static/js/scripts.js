$(document).ready(() => {

    $('#ciscoSpecs').on('click', () => {
        $('.brocadeOptions').hide();
        $('.hpOptions').hide();
        $('#brocadeSpecs').toggleClass('d-none');
        $('#hpSpecs').toggleClass('d-none');
        $('#ciscoSpecs').toggleClass('col-12');
        $('.ciscoOptions').slideToggle();
        $('.brocade6740').slideUp();
        $('.brocade6940').slideUp();
        $('.cisco93180').slideUp();
        $('.cisco9504').slideUp();
        $('.hp5900AF').slideUp();
    });

    $('#brocadeSpecs').on('click', () => {
        $('.ciscoOptions').hide();
        $('.hpOptions').hide();
        $('#ciscoSpecs').toggleClass('d-none');
        $('#hpSpecs').toggleClass('d-none');
        $('#brocadeSpecs').toggleClass('col-12');
        $('.brocadeOptions').slideToggle();
        $('.brocade6740').slideUp();
        $('.brocade6940').slideUp();
        $('.cisco93180').slideUp();
        $('.cisco9504').slideUp();
        $('.hp5900AF').slideUp();
    });

    $('#hpSpecs').on('click', () => {
        $('.ciscoOptions').hide();
        $('.brocadeOptions').hide();
        $('#brocadeSpecs').toggleClass('d-none');
        $('#ciscoSpecs').toggleClass('d-none')
        $('#hpSpecs').toggleClass('col-12');
        $('.hpOptions').slideToggle();
        $('.brocade6740').slideUp();
        $('.brocade6940').slideUp();
        $('.cisco93180').slideUp();
        $('.cisco9504').slideUp();
        $('.hp5900AF').slideUp();
    });

    $('.93180YC').on('click', () => {
        $('.brocade6940').slideUp();
        $('.brocade6740').slideUp();
        $('.cisco9504').slideUp();
        $('.cisco93180').slideToggle();
    });

    $('.C9504').on('click', () => {
        $('.brocade6740').slideUp();
        $('.brocade6940').slideUp();
        $('.cisco93180').slideUp();
        $('.hp5900AF').slideUp();
        $('.cisco9504').slideToggle();
    });

    $('.BR-VDX6740').on('click', () => {
        $('.cisco93180').slideUp();
        $('.cisco9504').slideUp();
        $('.brocade6940').slideUp();
        $('.hp5900AF').slideUp();
        $('.brocade6740').slideToggle();
    });

    $('.BR-VDX6940-144S').on('click', () => {
        $('.cisco93180').slideUp();
        $('.cisco9504').slideUp();
        $('.brocade6740').slideUp();
        $('.hp5900AF').slideUp();
        $('.brocade6940').slideToggle();
    });

    $('.5900AF-48XG-4QSFP+').on('click', () => {
        $('.cisco93180').slideUp();
        $('.cisco9504').slideUp();
        $('.brocade6740').slideUp();
        $('.brocade6940').slideUp();
        $('.hp5900AF').slideToggle();
    });


    $('#cacheListTable').dataTable( {
        "aaSorting": [[9,'desc']],
        "pageLength": 15,
        "lengthMenu": [[15, 30, 45, -1], [15, 30, 45, "All"]],
        "pagingType": "full_numbers",
        "columnDefs": [
          {
            className: "dt-nowrap", "targets": [ 0 ]
          },
        ],

    });

    $('#cachePortsOccupationTable').dataTable( {
        "aaSorting": [[4,'desc']],
        "pageLength": 15,
        "lengthMenu": [[15, 30, 45, -1], [15, 30, 45, "All"]],
        "pagingType": "full_numbers",
        "columnDefs": [
          {
            className: "dt-nowrap", "targets": [ 0 ]
          },
        ],
    });

    $('#cachePortsTrafficTable').dataTable( {
        "aaSorting": [[0,'asc']],
        "pageLength": 15,
        "lengthMenu": [[15, 30, 45, -1], [15, 30, 45, "All"]],
        "pagingType": "full_numbers",
        "columnDefs": [
          {
            className: "dt-nowrap", "targets": [ 0 ]
          },
        ],
    });

    $('#cacheUpdateMassive').on('submit', () => {
        $.ajax({
                  url:"/cache_update_massive",
                  method:"POST",
                  beforeSend:function() {
                   $('.btn').attr('disabled', 'disabled');
                   $('#process').css('display', 'block');
                  },
        })
    });

    $('#cacheUpdateRegister').on('submit', () => {
        $.ajax({
                  url:"/cache_update_register",
                  method:"POST",
                  beforeSend:function() {
                   $('.btn').attr('disabled', 'disabled');
                   $('#process').css('display', 'block');
                  },
        })
    });

    $('#cache_register').on('submit', function(event) {
        event.preventDefault();
        var count_error = 0;

        if(count_error == 0) {
           $.ajax({
              url:"/cache_register",
              method:"POST",
              data:$(this).serialize(),
              beforeSend:function()
              {
               $('.btn').attr('disabled', 'disabled');
               $('#process').css('display', 'block');
              },
              success:function(data)
              {
               var percentage = 0;
               var timer = setInterval(function(){
                percentage = percentage + 20;
                progress_bar_process(percentage, timer,data);
               }, 1000);
              }
             })
          }
          else {
           return false;
          }

    });

    function progress_bar_process(percentage, timer, data) {
        $('.progress-bar').css('width', percentage + '%');

        if(percentage > 100) {
             clearInterval(timer);
             $('#cache_register')[0].reset();
             $('#process').css('display', 'none');
             $('.progress-bar').css('width', '0%');
             $('.btn').attr('disabled', false);
             $('#success_message').html(data);

             setTimeout(function() {
              $('#success_message').html('');
             }, 5000);
        }

	}

});
