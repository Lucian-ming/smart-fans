/**
 * 조건에 맞는 배열 제거
 * @param {string} deleteValue 제거하고 싶은 배열 값
 * @return {array}
 */
Array.prototype.clean = function (deleteValue) {
    for (var idx = 0; idx < this.length; idx++) {
        if (this[idx] === deleteValue) {
            this.splice(idx, 1);
            idx--;
        }
    }
    return this;
};

/**
 * 숫자 단위 변환
 * @param {string} currentUnit 현재 실제 숫자 단위(G, M, k ...) standardUnit 배열에 있는 단위, 없으면 추가해서 사용. 단, 10^3 기준의 단위만 사용
 * @param {string} useUnit 사용할 단위(ohm, P, F, Hz ...)
 * @param {array} aRange 기준 단위 유지 범위(표현 되는 기존 단위를 어떤 자리에서 변환할 지 설정) - 생략시 10^3 기준으로 단위 변환
 * @return {string} ex) {345} + {k} + {ohm} = '345kohm'
 */
Number.prototype.convertUnit = function (currentUnit, useUnit, aRange) {
    currentUnit = currentUnit || '';
    useUnit = useUnit || '';
    var convertValue, resultUnit, result;
    var crtValue = this; // 현재 값
    var n = 0; // 현재 위치 계산용
    var sign = 1; // 음수 체크
    var setDecimal = 5; // 소수점 표현 자릿수
    var standardUnit = ['G', 'M', 'k', '', 'm', 'u', 'n', 'p']; // 표현하고 싶은 단위(10^3 기준, 큰 단위부터 나열)
    var crtU = standardUnit.indexOf(currentUnit); // 기준 단위
    var chkCalRange = {
        min: crtU - n,
        max: (standardUnit.length - 1) - crtU
    }; // 범위 설정

    // 음수 체크
    if (0 > crtValue) {
        crtValue = Math.abs(crtValue);
        sign = -1;
    }

    // 단위 변환 - 정해진 단위(standardUnit) 범위를 넘어가면 정해놓은 범위의 마지막 단위 유지
    function cvt(value) {
        if (value >= 1000 && n + chkCalRange.min > 0) { // 정해진 단위 범위일 때

            // 1. 기본 10^3 단위 변환
            // 2. 소수점 10^3, 10^5 단위로 변환
            // 3. 기본 단위 범위 확장 10^5, 그 이후 범위는 10^5

            value = value / 1000;
            n--;

            return cvt(value);
        } else if (n < chkCalRange.max && aRange && aRange.length > 1) { // 정해진 단위 범위면서 소수 점 단위변환 기준이 다를 때
            // 2. 소수점 10^3, 10^5 단위로 변환

            if (n === 0 && 1 > value) { // 소수점 첫번째 단위 변환
                value = value * 1000;
                n++;

                return cvt(value);
            } else if (Math.pow(0.1, aRange[1].toFixed(aRange[1] - 1) * 1) > value) {
                value = value * 1000;
                n++;

                return cvt(value);
            } else {
                return value.toFixed(aRange[1]);
            }
        } else if (n < chkCalRange.max) { // 정해진 단위 범위일 때

            // 1. 기본 10^3 단위 변환
            // 3. 기본 단위 범위 확장 10^5, 그 이후 범위는 10^5

            if (1 > value) { // 소수점 첫번째 단위 변환
                value = value * 1000;
                n++;

                return cvt(value);
            } else {
                return value.toFixed(setDecimal);
            }

        } else { // 정해진 단위 범위를 벗어날 때 - 마지막 단위를 유지

            // 1. 기본 10^3 단위 변환
            // 2. 소수점 10^3, 10^5 단위로 변환
            // 3. 기본 단위 범위 확장 10^5, 그 이후 범위는 10^5

            return value.toFixed(setDecimal);
        }
    }

    // 기존 단위 유지 기준 설정

    // 3. 기본 단위 범위 확장 10^5, 그 이후 범위는 10^5

    if (aRange && aRange.length === 1) {
        var dec = {
            min: Math.pow(0.1, aRange[0]).toFixed(setDecimal) * 1,
            max: Math.pow(10, aRange[0])
        };

        if (crtValue >= dec.max || crtValue < dec.min) {
            convertValue = cvt(crtValue) * sign; // 최종 값 {number}
        } else {
            convertValue = crtValue.toFixed(setDecimal) * sign; // 최종 값 {number}
        }
    } else {
        convertValue = cvt(crtValue) * sign; // 최종 값 {number}
    }

    resultUnit = crtU + n; // standardUnit 배열 순서 = 최종 변환 단위 {number}
    result = convertValue + standardUnit[resultUnit] + useUnit; // {number} + {string} + {string} = {345}{k}{ohm} = 345kohm

    /* 값이 0인 경우 기본 단위로 표시 */
    if (convertValue === 0) {
        result = convertValue + useUnit;
    }

    return result;
};

var SEM = SEM || {}; // 네임스페이스 설정

SEM.chart = {
    isRun: false,
    isRunSimul: false,
    chartOriginData: {}, // 열려 있는 레이어 차트 원본 데이터
    chartTempObj: {}, // 생성된 차트 보관
    chartTempIdx: 1, // 생성된 차트 인덱싱
    chartLayerIdx: 1, // 노출 레이어 인덱싱 - 레이어 위치
    chartColors: [
        'rgb(237, 27, 36)',
        'rgb(0, 176, 240)',
        'rgb(255, 184, 15)',
        'rgb(0, 176, 80)',
        'rgb(243, 101, 35)',
        'rgb(0, 45, 86)',
        'rgb(231, 15, 144)',
        'rgb(17, 40, 255)',
        'rgb(89, 15, 15)',
        'rgb(141, 222, 72)',
        'rgb(237, 91, 99)',
        'rgb(141, 38, 170)',
        'rgb(21, 191, 165)',
        'rgb(224, 187, 30)',
        'rgb(194, 100, 125)',
        'rgb(65, 111, 149)',
        'rgb(255, 145, 226)',
        'rgb(146, 158, 248)',
        'rgb(184, 101, 50)',
        'rgb(133, 69, 255)',
        'rgb(240, 144, 168)',
        'rgb(199, 40, 50)',
        'rgb(35, 78, 186)',
        'rgb(61, 73, 59)'
    ],
    chartOptions: {
        animation: {
            duration: 0, // general animation time
        },
        hover: {
            animationDuration: 0, // duration of animations when hovering an item
        },
        responsiveAnimationDuration: 0,
        title: {
            display: false
        },
        onResize: function (me, newSize) {
            var semChart = SEM.chart;
            var chartIndex = me.id + 1;
            var $thisChart = semChart.chartTempObj[chartIndex];

            $thisChart.update();
            semChart.setGridLines(chartIndex);
        },
        maintainAspectRatio: false,
        tooltips: {
            mode: 'nearest',
            displayColors: false, // 라벨 값 심볼
            backgroundColor: 'rgb(255, 255, 255)',
            titleFontSize: 12,
            titleFontStyle: 'bold',
            titleFontColor: 'rgb(0, 0, 0)',
            titleSpacing: 2,
            titleMarginBottom: 8,
            bodySpacing: 6,
            bodyFontColor: '#000',
            xPadding: 23,
            yPadding: 10,
            cornerRadius: 0,
            borderWidth: 1,
            borderColor: '#000',
            callbacks: {
                title: function (tooltipItems, data) {
                    var idx = tooltipItems[0].datasetIndex;

                    return [data.datasets[idx].label];
                }
                // labelTextColor: function (tooltipItem, chart) {
                //     var idx = tooltipItem.datasetIndex;
                //     var c = SEM.chart.chartColors[idx];

                //     chart.options.tooltips.borderColor = c;

                //     return 'rgb(0, 0, 0)';
                // }
            }
        },
        scales: {
            xAxes: [{
                type: 'linear', // 축 타입
                ticks: { // 축의 값 커스텀
                    autoSkip: false, // 축 자동 생략
                    padding: 10
                },
                scaleLabel: {
                    display: true,
                    labelString: 'X축 제목'
                },
                gridLines: {
                    drawTicks: false
                }
            }],
            yAxes: [{
                type: 'linear', // 축 타입
                ticks: {
                    autoSkip: false, // 축 자동 생략
                    padding: 10
                },
                scaleLabel: {
                    display: true,
                    labelString: 'Y축 제목'
                },
                gridLines: {
                    drawTicks: false
                }
            }]
        },
        legend: {
            display: false // 기본 범례 노출
        },
        legendCallback: function (chart) { // 범례 커스텀
            // 개별 옵션에서 설정
            return '';
        },
        annotation: {
            annotations: []
        }
    },
    /**
     * 데이터 요청
     */
    requestData: function () {
        var requestData = confirm('不支持该项目。是否请求该数据？');

        if (requestData) {
            // 요청보내기
            var link = $("#web_outsitelink").val();
            window.open(link + "/cn/support/contact-us/inquiry/product.do?weblibrary=Y", "_blank");
        }
    },
    saveData: function (target) {
        $("#saveDataForm").empty();
        var semChart = this;
        var $ul = $(target).closest('.layer_cont_inner').children('.chart_label').find('ul');
        var graphType = $ul.find('[id^="saveDataGraphType"]').val();
        var simulationType = $ul.find('[id^="saveSimulationType"]').val();
        var $li = $ul.children('li.on');
        var html = '';

        if ($li.length <= 0 || $li.length <= 0) {
            alert("对不起，不支持该设置。 ");
            return;
        }

        html = '<input type="hidden" name="graphType" value="' + graphType + '"/>';
        html += '<input type="hidden" name="simulationType" value="' + simulationType + '"/>';

        /***************개발팀 추가************/
        if (simulationType == 'EfficiencyLoss' || simulationType == 'SimpleRipple') {
            var converterType = $ul.find('[id^="saveConverter"]').val();
            var modulation = $ul.find('[id^="saveModulation"]').val();
            var vin = $ul.find('[id^="saveVin"]').val();
            var vout = $ul.find('[id^="saveVout"]').val();
            var frequency = $ul.find('[id^="saveFrequency"]').val();
            var adc = $ul.find('[id^="saveAdc"]').val();
            var swRise = $ul.find('[id^="saveSwRise"]').val();
            var swRon = $ul.find('[id^="saveSwRon"]').val();
            var standardType = $("#selectedPartsTool").attr('data-type') === 'default-inductor' ? 'Inductor' : 'Capacitor';

            html += '<input type="hidden" name="converterType" value="' + converterType + '"/>';
            html += '<input type="hidden" name="modulation" value="' + modulation + '"/>';
            html += '<input type="hidden" name="vin" value="' + vin + '"/>';
            html += '<input type="hidden" name="vout" value="' + vout + '"/>';
            html += '<input type="hidden" name="frequency" value="' + frequency + '"/>';
            html += '<input type="hidden" name="adc" value="' + adc + '"/>';
            html += '<input type="hidden" name="swRise" value="' + swRise + '"/>';
            html += '<input type="hidden" name="swRon" value="' + swRon + '"/>';
            html += '<input type="hidden" name="standardType" value="' + standardType + '"/>';

            if (standardType == 'Inductor') {
                html += '<input type="hidden" name="inductorList[0].vPartNumber" value="' + $ul.find('[id^="saveStandard-part"]').val() + '"/>';

                if (graphType == 'InductorLoss') {
                    $ul.find('li[data-parts-gsubtype=ACLoss]').each(function (i, item) {
                        html += '<input type="hidden" name="capacitorList[' + i + '].vPartNumber" value="' + $(item).attr('data-parts') + '"/>';
                        html += '<input type="hidden" name="capacitorList[' + i + '].capCnt" value="' + $(item).attr('data-parts-cnt') + '"/>';
                    });
                } else {
                    $li.each(function (i, item) {
                        html += '<input type="hidden" name="capacitorList[' + i + '].vPartNumber" value="' + $(item).attr('data-parts') + '"/>';
                        html += '<input type="hidden" name="capacitorList[' + i + '].capCnt" value="' + $(item).attr('data-parts-cnt') + '"/>';
                    });
                }

            } else if (standardType == 'Capacitor') {

                html += '<input type="hidden" name="capacitorList[0].vPartNumber" value="' + $ul.find('[id^="saveStandard-part"]').val() + '"/>';
                html += '<input type="hidden" name="capacitorList[0].capCnt" value="' + $ul.find('[id^="saveStandard-cnt"]').val() + '"/>';

                if (graphType == 'InductorLoss') {
                    $ul.find('li[data-parts-gsubtype=ACLoss]').each(function (i, item) {
                        html += '<input type="hidden" name="inductorList[' + i + '].vPartNumber" value="' + $(item).attr('data-parts') + '"/>';
                    });
                } else {
                    $li.each(function (i, item) {
                        html += '<input type="hidden" name="inductorList[' + i + '].vPartNumber" value="' + $(item).attr('data-parts') + '"/>';
                    });
                }
            }
            /**********************************/
        } else {
            if ($ul.find('[id^="savesParamCircuit"]').length > 0) {
                html += '<input type="hidden" name="sParamCircuit" value="' + $ul.find('[id^="savesParamCircuit"]').val() + '"/>';
            }

            $li.each(function (i, item) {
                html += '<input type="hidden" name="paramList[' + i + '].partNumber" value="' + $(item).find('input[name="partNumber"]').val() + '"/>';

                if ($(item).find('input[name="vdc"]').length > 0) { //MLCC,TANTALUM
                    html += '<input type="hidden" name="paramList[' + i + '].vdc" value="' + $(item).find('input[name="vdc"]').val() + '"/>';
                }

                if ($(item).find('input[name="adc"]').length > 0) { //BEAD,PI,HFI
                    html += '<input type="hidden" name="paramList[' + i + '].adc" value="' + $(item).find('input[name="adc"]').val() + '"/>';
                }

                if ($(item).find('input[name="degC"]').length > 0) {
                    html += '<input type="hidden" name="paramList[' + i + '].degC" value="' + $(item).find('input[name="degC"]').val() + '"/>';
                }

                if ($(item).find('input[name="modelTypeOne"]').length && simulationType == 'TEMPDC') {
                    html += '<input type="hidden" name="paramList[' + i + '].modelTypeOne" value="' + $(item).find('input[name="modelTypeOne"]').val() + '"/>';
                }

                if (graphType == 'ANvsFreq' || graphType == 'ANvsVdc') {
                    html += '<input type="hidden" name="paramList[' + i + '].mountingTypeOne" value="' + $(item).find('input[name="mountingTypeOne"]').val() + '"/>';
                    html += '<input type="hidden" name="paramList[' + i + '].solderTypeOne" value="' + $(item).find('input[name="solderTypeOne"]').val() + '"/>';
                }
            });
        }
        $('#saveDataForm').append('<input type="hidden" name="_csrf" value="' + $('input[name="_csrf"]').val() + '"/>' );
        $("#saveDataForm").append(html);
        $("#saveDataForm").submit();

    },
    downloadImg: function (target) {
        var $chartWrap = $(target).closest('.layer_cont');
        var $captureWrap = $chartWrap.find('.layer_cont_inner'); // 프린트 영역
        var $ul = $(target).closest('.layer_cont_inner').children('.chart_label').find('ul');
        var $li = $ul.children('li.on');

        if ($li.length <= 0 || $li.length <= 0) {
            alert("对不起，不支持该设置。 ");
            return;
        }

        $captureWrap.addClass("capture_chart_layer");

        html2canvas($captureWrap[0], {
            allowTaint: true
        }).then(function (canvas) {
            $captureWrap.removeClass("capture_chart_layer");

            if (typeof FlashCanvas != "undefined") {
                FlashCanvas.initElement(canvas);
            }

            var url = canvas.toDataURL("image/png");

            $("#imgData").val(url);
            $("#imgForm").submit();

        });
    },
    printLayer: function (target) {
        var $chartWrap = $(target).closest('.layer_cont');
        var $captureWrap = $chartWrap.find('.canvas_wrap'); // 프린트 영역
        var $ul = $(target).closest('.layer_cont_inner').children('.chart_label').find('ul');
        var $li = $ul.children('li.on');

        if ($li.length <= 0 || $li.length <= 0) {
            alert("对不起，不支持该设置。 ");
            return;
        }

        $captureWrap.addClass("capture_chart_layer");

        html2canvas($captureWrap[0], {
            allowTaint: true
        }).then(function (canvas) {
            $captureWrap.removeClass("capture_chart_layer");

            if (typeof FlashCanvas != "undefined") {
                FlashCanvas.initElement(canvas);
            }

            var url = canvas.toDataURL("image/png");
            var win = null;

            win = window.open('', 'title', 'scrollbars=no,toolbar=no,resizable=no,width=1200,height=780,left=0,top=0');
            win.document.write('<html>');
            win.document.write('<head>');
            win.document.write('    <link rel="stylesheet" href="./resource/css/style.css">');
            win.document.write('</head>');
            win.document.write('<body>');
            win.document.write('    <img src="' + url + '" style="max-width:100%;">');
            win.document.write('</body>');
            win.document.write('</html>');
            win.document.close();
            win.focus();

            setTimeout(function () {
                win.print();
                win.close();
            }, 5);

            return true;
        });
    },
    /**
     * 차트 레이어 창 개수 제한
     * @function SEM.chart.limitLayer
     * @param {number} max 레이어 최대 개수
     * @return {boolean}
     */
    limitLayer: function (max) {
        var semChart = this;
        var _size = document.querySelectorAll('.layer_chart').length;

        if (_size >= max) {
            alert('最多能生成' + max + '个窗口。');
            if ($('#toggleGraph').length) {
                semChart.toggleChart.show();
                $('#toggleGraph').prop('checked', true); // 차트 토글 버튼 on
            }
            return false;
        }

        return true;
    },
    /**
     * partslist 속성 초기화 :: Simulation Tool
     * @param {string} target partslist 부모 ID 값
     */
    resetPartlistAttr: function (target) {
        if (!document.getElementById(target)) return;
        var $el = document.getElementById(target);
        var $list = $el.querySelectorAll('li'); // li로 검색, partslist가 아닌 다른 li 존재할 경우 수정 필요할 수 있음.
        var _length = $list.length;

        for (var i = 0; i < _length; i++) {
            $list[i].removeAttribute('data-request');
        }
    },
    /**
     * 그래프 on/off :: Simulation Tool
     */
    toggleChart: {
        show: function () {
            $('body').removeClass('chart_off');
        },
        hide: function () {
            $('body').addClass('chart_off');
        }
    },
    /**
     * 통신
     * @function SEM.chart.transferSimulTool
     * @param {object} infoData 넘겨줄 데이터 request data
     * @param {string} graphType 선택한 그래프 유형
     */
    transferSimulTool: function (infoData, graphType) {
        var semChart = this;

        $.ajax({
            url: "/converterGraph/checkSimpleRipplePreRange.do",
            type: "POST",
            dataType: "json",
            timeout: 30000,
            data: JSON.stringify(infoData),
            contentType: "application/json",
            beforeSend: function(xhr){
				 var token = $('input[name="_csrf"]').val();
	            var header =  $('input[name="_csrf_header"]').val();
	            
	            xhr.setRequestHeader(header, token);
			},
            complete: function () {

            },
            success: function (data, status, xhr) {
                semChart.isRunSimul = false; // 차트 실행 가능으로 변경
                semChart.validationSimulTool(graphType, data);

            },
            error: function (jqXHR, textStatus, errorThrown) {
                semChart.isRunSimul = false; // 차트 실행 가능으로 변경
                alert("您要求处理中遇到了问题。");

            }
        });
    },
    /**
     * 유효성 체크 :: Simulation Tool
     * @param {string} type 선택한 그래프 타입
     * @param {array} partData Isat, Resolution 범위를 벗어난 파트 배열
     */
    validationSimulTool: function (type, partData) {
        var _popupFlag = true;
        var _html = []; // 범위 벗어난 파트 목록
        var vinMin, vinMax, voutMin, voutMax, freqMin, freqMax, adcMin, adcMax, isatExceptList, pfmExceptList;
        $('#graphTypeBtn').find('.btn').data('chartType', type); // 선택한 그래프 타입 정보 담기
        var vin = Number(document.getElementById('converterVin').value);
        var vout = Number(document.getElementById('converterVout').value);
        var frequency = Number(document.getElementById('converterFreq').value);
        var adc = Number(document.getElementById('converterAdc').value);

        if (partData) {
            isatExceptList = partData.isatExceptList; // Isat 예외 목록
            pfmExceptList = partData.pfmExceptList; // Resolution 예외 목록
        }

        /* 유효성 체크 계산 */
        var _partsName;
        var selectedArr = []; // 파트 목록
        var $spt = document.getElementById('selectedPartsTool');
        var standardType = $spt.getAttribute('data-type');
        var $cpct = document.getElementById('selectedCapacitor');
        var cpctList = $cpct.querySelectorAll('li.on');
        var $indt = document.getElementById('selectedInductor');
        var indtList = $indt.querySelectorAll('li.on');

        /**
         * 배열 병합
         * @param {array [,array, array, ...]} 병합할 배열들, 인자 제한 없음
         */
        var mergeArray = function () {
            var _argLength = arguments.length;
            var temp = [];

            for (var argIdx = 0; argIdx < _argLength; argIdx++) {
                var el = arguments[argIdx];
                var _elLength = el.length;

                for (var elIdx = 0; elIdx < _elLength; elIdx++) {
                    var elArr = el[elIdx];

                    temp.push(elArr);
                }
            }

            return temp;
        };

        /* 기준 타입 선정렬 */
        if (standardType === 'default-capacitor') {
            selectedArr = mergeArray(cpctList, indtList);
        } else {
            selectedArr = mergeArray(indtList, cpctList);
        }

        /* 범위를 벗어난 항목들 표시 */
        var _length = selectedArr.length; // 파트 목록
        var _listAddFlag = true; // 통합 레이어창 표시 여부
        var _dutyFlag = true; // Vout 로직 진행 결정
        var _loadFlag = true; // Isat 로직 진행 결정

        var _htmlItem = []; // 범위를 벗어난 입력값 목록
        var ratedVMax;
        // var lCurrentMax;

        /**
         * 목록 비교
         * @param {array} list 비교할 목록
         * @param {string} name 비교할 값
         */
        var compareList = function (list, name) {
            var compareResult = true;
            var _length = list.length;

            for (var idx = 0; idx < _length; idx++) {
                var _part = list[idx];
                if (_part === name) {
                    compareResult = false;
                }
            }

            return compareResult;
        };

        for (var idx = 0; idx < _length; idx++) {
            var el = selectedArr[idx];
            _listAddFlag = true; // flag 초기화, 한개의 항목이라도 범위를 넘어간다면 false
            _dutyFlag = true; // flag 초기화, Vout 로직 진행 결정
            _loadFlag = true; // flag 초기화, Isat 로직 진행 결정
            _htmlItem = []; // 범위를 벗어난 항목들 초기화
            ratedVMax = Number(el.getAttribute('data-vmax')); // Cap ratedV max [Vout]
            _partsName = el.querySelector('.parts_checkbox').value;
            lCurrentMax = Number(el.getAttribute('data-currentmax')); // Lcurrent 그래프 max [Adc]

            /**
             * Duty :: Vin
             * 유효값: min 이상, max 이하
             */
            vinMin = vout / 0.9;
            vinMax = vout / 0.1;
            if (vinMin > vin || vin > vinMax) { // 이상, 이하
                _htmlItem.push('        <span class="item">占空比</span>');
                _dutyFlag = false;
                _listAddFlag = false;
            }

            /**
             * Vout
             * 유효값: min 이상, max 이하
             */
            if (_dutyFlag) {
                voutMin = vin * 0.1;
                voutMax = vin * 0.9;
                if (ratedVMax) {
                    voutMax = voutMax > ratedVMax ? ratedVMax : voutMax; // voutMax 값이 ratedVMax 값 보다 클 경우에만 ratedVMax 값 적용
                }
                if (voutMin > vout || vout > voutMax) { // 이상, 이하
                    _htmlItem.push('        <span class="item">输出电压</span>');
                    _listAddFlag = false;
                }
            }

            /**
             * Load :: Adc
             * 유효값: min 이상, max 이하
             */
            adcMin = 0.01;
            adcMax = 8;
            if (lCurrentMax) {
                adcMax = adcMax > lCurrentMax ? lCurrentMax : adcMax; // adcMax 값이 lCurrentMax 값 보다 클 경우에만 lCurrentMax 값 적용
            }
            if (adcMin > adc || adc > adcMax) { // 이상, 이하
                _htmlItem.push('        <span class="item">负载</span>');
                _loadFlag = false;
                _listAddFlag = false;
            }

            /**
             * Isat
             * backend에서 유효하지 않은 파트 전달 {array}
             */
            if (_loadFlag) {
                if (isatExceptList) {
                    var resultIsat = compareList(isatExceptList, _partsName);

                    if (!resultIsat) {
                        _htmlItem.push('        <span class="item">饱和电流</span>');
                        _listAddFlag = false;
                    }
                }
            }

            /**
             * Frequency
             * 유효값: min 이상, max 이하
             */
            freqMin = 0.01;
            freqMax = 10;
            if (freqMin > frequency || frequency > freqMax) { // 이상, 이하
                _htmlItem.push('        <span class="item">频率</span>');
                _listAddFlag = false;
            }

            /**
             * Resolution
             * backend에서 유효하지 않은 파트 전달 {array}
             */
            if (pfmExceptList) {
                var resultResolution = compareList(pfmExceptList, _partsName);

                if (!resultResolution) {
                    _htmlItem.push('        <span class="item wide">分辨率</span>');
                    _listAddFlag = false;
                }
            }

            _htmlItem = _htmlItem.join('\n');

            /* 범위를 벗어난 항목이 한개라도 존재하면 팝업내 목록에 표시 */
            if (!_listAddFlag) {
                _html.push('<li>');
                _html.push('    <div class="partname">' + _partsName + ' </div>');
                _html.push('    <div class="condition">');
                _html.push(_htmlItem); // 범위를 벗어난 항목들
                _html.push('    </div>');
                _html.push('</li>');

                el.setAttribute('data-request', 'false'); // 해당 partslist 데이터 전송하지 않게 처리

                _popupFlag = false; // 팝업 띄우기
            }
        }

        _html = _html.join('\n');

        /* 범위를 벗어난 항목이 존재하면 팝업 생성 */
        if (_popupFlag) {
            $('#graphTypeBtn').find('.btn').trigger('click'); // 알림 팝업 버튼 트리거
        } else {
            $('#conditionItemList').empty(); // 목록 초기화
            $('#conditionItemList').append(_html); // 범위를 벗어난 항목 표시
            $('.layer_condition_wrap').addClass('open'); // 알림 팝업 오픈
            var $layer = $('#layerCondition');
            var $window = $(window);
            $layer.removeAttr('style'); // 설정 값 초기화
            var _bodyWidth = $window.width();
            var _bodyHeight = $window.height();
            var _w = $layer.outerWidth();
            var _h = $layer.outerHeight();
            var offsetX = (_bodyWidth - _w) / 2;
            var offsetY = (_bodyHeight - _h) / 2;
            $layer.css({
                'top': offsetY,
                'left': offsetX
            }); // 위치 중앙 초기화
        }
    },
    /**
     * 파트 선택 유효성 검사
     * @function SEM.chart.validationSelectedParts
     * @return {boolean}
     */
    validationSelectedParts: function () {
        var $item;

        if (document.getElementById('converterType')) {
            //Converter Simulation Tool
            var $selectedParts = $('#selectedPartsTool');
            var $selectedInductor = $('#selectedInductor');
            var $selectedCapacitor = $('#selectedCapacitor');
            var selectedInductor = $selectedInductor.find('input:checkbox[name="partsChk"]').length; // 선택된 목록 :: Inductor
            var selectedCapacitor = $selectedCapacitor.find('input:checkbox[name="partsChk"]').length; // 선택된 목록 :: Capacitor
            var checkedInductor = $selectedInductor.find('input:checkbox[name="partsChk"]:checked').length; // 체크된 목록 :: Inductor
            var checkedCapacitor = $selectedCapacitor.find('input:checkbox[name="partsChk"]:checked').length; // 체크된 목록 :: Capacitor
            var standardType = $selectedParts.attr('data-type');

            if (standardType === 'default-inductor') {
                if (selectedInductor < 1) {
                    alert('请从下方列表中选择电感型号');
                    return false;
                }
                if (selectedCapacitor < 1) {
                    alert('请从下方列表中选择电容型号');
                    return false;
                }
                if (checkedInductor < 1) {
                    alert('请从选定区域选择电感');
                    return false;
                }
                if (checkedCapacitor < 1) {
                    alert('请从选定区域选择电容');
                    return false;
                }
            } else if (standardType === 'default-capacitor') {
                if (selectedCapacitor < 1) {
                    alert('请从下方列表中选择电容型号');
                    return false;
                }
                if (selectedInductor < 1) {
                    alert('请从下方列表中选择电感型号');
                    return false;
                }
                if (checkedCapacitor < 1) {
                    alert('请从选定区域选择电容');
                    return false;
                }
                if (checkedInductor < 1) {
                    alert('请从选定区域选择电感');
                    return false;
                }
            }
        } else {
            //MLCC
            $item = $('input:checkbox[name="partsChk"]:checked');

            if ($('#selectedList').children('li').length <= 0 || $item.length <= 0) {
                alert('请选择器件型号');
                return false;
            }
        }

        return true;
    },
    /**
     * 차트 로딩 여부 체크
     * @function SEM.chart.chartRun
     * @return {boolean}
     */
    chartRun: function () {
        if (SEM.chart.isRun || SEM.chart.isRunSimul) {
            alert('再次仿真后再尝试。');
            return false;
        }

        return true;
    },
    /**
     * 이벤트 등록
     * @function SEM.chart.eventListener
     */
    eventListener: function () {
        var semChart = this;

        /* 차트 실행 */
        $('#graphTypeBtn .btn').on('click', function () {
            if (semChart.chartRun() && semChart.limitLayer(10) && semChart.validationSelectedParts()) {
                SEM.chart.isRun = true; // 차트 실행 불가능으로 변경

                var graphType = {}; // 차트 유형 obj | graphType, sParamCircuit

                graphType.chartType = $(this).data('chartType'); // 차트 유형

                if ($(this).data('circuitType')) {
                    graphType.circuitType = $(this).data('circuitType'); // sParamCircuit 유형
                }
                semChart.settingChart(graphType); // 차트 생성
            }
            if (document.getElementById('converterType')) {
                $('.layer_condition_wrap').removeClass('open');
            }
        });

        /* Simulation Tool */
        $('#simulationBtn').find('.btn').on('click', function () {
            if (semChart.chartRun() && semChart.limitLayer(10) && semChart.validationSelectedParts()) {
                SEM.chart.isRunSimul = true; // 차트 실행 불가능으로 변경
                var _self = $(this);
                var graphType = _self.data('chartType');

                if (graphType === 'InductorVoltage' || graphType === 'InductorCurrent' || graphType === 'RippleVoltage') {
                    /* Isat 체크 통신 */
                    var typeObj = { chartType: graphType }; // getInfoData 메서드에 맞는 인자 설정
                    var _valiData = semChart.getInfoData(typeObj); // request data
                    semChart.transferSimulTool(_valiData, graphType); // 계산 데이터
                } else {
                    /* 추가 통신이 필요하지 않을 때 */
                    SEM.chart.isRunSimul = false; // 차트 실행 가능으로 변경
                    semChart.validationSimulTool(graphType);
                }
            }
        });

        /* 그래프 on/off */
        $('#toggleGraph').on('change', function () {
            var _self = $(this);
            var chkStatus = _self.prop('checked');

            if (!$('.layer_chart').length) {
                alert('没有图形可以显示。');
                _self.prop('checked', false);
                return;
            }

            if (chkStatus) {
                semChart.toggleChart.show();
            } else {
                semChart.toggleChart.hide();
                semChart.arrangeLayer(); // 레이어 재정렬
            }

            gtag('event', 'select_graph_onoff', { 'event_category': 'CST', 'event_label': 'SEM_CL_W' }); // Google Analytics
        });

        $('#layerCondition').draggable({
            containment: '#wrap', // 레이어 이동 범위 설정
            scroll: true,
            handle: '#layerCdtTit'
        });

        /* 파트 스위칭 :: Simulation Tool */
        var $inductor_selected = $("#inductor_selected"),
            $capacitor_selected = $("#capacitor_selected");
        var _single = '* 请选择器件型号';
        var _multi = '* 请选择器件型号';
        var selectedParts = {
            inductor: function () {
                $inductor_selected.find('.empty_txt').text(_single);
                $capacitor_selected.find('.empty_txt').text(_multi);
                $('#selectedPartsTool').attr('data-type', 'default-inductor');
                $inductor_selected.find(".list_del").each(function (index, item) {
                    if (index != 0) $(item).trigger("click");
                });
                $inductor_selected.find(".total").text(1);
                $capacitor_selected.find(".total").text($('#selectedPartsTool').attr("data-cmax"));
            },
            capacitor: function () {
                $inductor_selected.find('.empty_txt').text(_multi);
                $capacitor_selected.find('.empty_txt').text(_single);
                $('#selectedPartsTool').attr('data-type', 'default-capacitor');
                $capacitor_selected.find(".list_del").each(function (index, item) {
                    if (index != 0) $(item).trigger("click");
                });
                $capacitor_selected.find(".total").text(1);
                $inductor_selected.find(".total").text($('#selectedPartsTool').attr("data-imax"));
            }
        };

        /* 기준 변환 */
        $('#btnSwitch').on('click', function () {
            var _c = confirm('选择的部件和图形将被初始化。是否继续? ');

            if (!_c) {
                return false;
            }

            /* 모든 차트 데이터 삭제 */
            var _chartData = semChart.chartOriginData;
            for (var key in _chartData) {
                if (_chartData.hasOwnProperty(key)) {
                    semChart.closeLayer(key);
                    semChart.removeChartData(key);
                }
            }

            var $selectedPartsTool = $('#selectedPartsTool');
            var _dataType = $selectedPartsTool.attr('data-type');

            if (_dataType === 'default-inductor') {
                selectedParts.capacitor();
            } else {
                selectedParts.inductor();
            }
        });

        /* 설정 영역 외 클릭시 닫기 */
        $('body').on('click', function (event) {
            var $this = $(event.target);
            if (!$this.hasClass('layer_tool_setting') && $this.closest('.input_axes').length < 1) {
                $('.layer_chart .input_axes').removeClass('on');
            }
        });
    },
    /**
     * 차트 초기화
     * @function SEM.chart.initChart
     * @param {number} chartIndex 차트 번호
     */
    initChart: function (chartIndex) {
        var semChart = this;
        var $thisChart = semChart.chartTempObj[chartIndex];
        var $thisChartLayer = $('.layer_chart[data-chart-index="' + chartIndex + '"]'); // 해당 차트 레이어
        var chartType = $thisChartLayer.data('chartType');
        var typeInfo = semChart.getTypeInfo(chartType);

        /* 축 기본 설정으로 변경 */
        function initAxes(axis) {
            var options = {}; // 변환에 필요한 정보
            var axisType = typeInfo.axesType[axis];
            var convertAxisType = axisType === 'logarithmic' ? 'Log' : 'Linear'; // 해당 ID값으로 변환
            var _t = '[id^=chart' + axis.toUpperCase() + convertAxisType + ']'; // 해당 라디오 버튼

            options.axes = axis;
            options.axesType = axisType;
            options.chartType = chartType;
            options.chartIndex = chartIndex;

            semChart.setAxesType(options); // 축 설정
            $thisChartLayer.find(_t).prop('checked', true); // 축 옵션창 라디오 버튼 기본 설정으로 변경
        }

        initAxes('x');
        initAxes('y');
    },
    /**
     * Y축 데이터로 차트 sort
     * @function SEM.chart.sortYData
     * @param {string} type sParamType or asixOption
     * @param {number} chartIndex 대상 차트 번호
     */
    sortYData: function (type, chartIndex) {
        var semChart = this;
        var $thisChart = semChart.chartTempObj[chartIndex];
        var $thisChartLayer = $('.layer_chart[data-chart-index="' + chartIndex + '"]'); // 해당 차트 레이어
        var chartType = $thisChartLayer.data('chartType');
        var typeInfo = semChart.getTypeInfo(chartType);
        var meta;
        var datasets = $thisChart.config.data.datasets;
        var selectYData = typeInfo.selectYData();

        for (var i = 0; i < datasets.length; i++) {
            var currentData = datasets[i];
            meta = $thisChart.getDatasetMeta(i);
            meta.hidden = true; // 차트 라인 hide

            if (currentData.hasOwnProperty('sParamType')) {
                if (currentData.sParamType === type) meta.hidden = null; // 차트 라인 show
            } else if (currentData.hasOwnProperty('asixYOption')) {
                if (currentData.asixYOption === type) meta.hidden = null; // 차트 라인 show
            }
        }

        // y축 타이틀 설정
        $thisChart.config.options.scales.yAxes[0].scaleLabel.labelString = selectYData.title[type];

        // 범례 show/hide
        $thisChartLayer.find('.chart_label li').hide();
        $thisChartLayer.find('.chart_label li').removeClass('on');
        $thisChartLayer.find('.chart_label li[data-param-type="' + type + '"]').addClass('on').show();

        if (chartType !== 'Smithchart') {
            semChart.setGridLines(chartIndex);
        } else {
            $thisChart.update(); // 2019-04-09 주석 처리 복구, 업데이트 함수 필요함.
        }
    },
    /**
     * 그래프 상단 추가 정보 갱신 :: Simulation Tool
     * @function SEM.chart.updateSubInfo
     * @param {object} target 해당 레이어
     */
    updateSubInfo: function (target) {
        var $li = target.find('.chart_label').find('li.on').eq(0);
        var _color = $li.css('color');
        var _subInfo = $li.data('partsSubinfo');

        target.find('.sub_info').find('.val').text(_subInfo);
        target.find('.sub_info').css('color', _color);
    },
    /**
     * 범례 삭제
     * @function SEM.chart.removeLegend
     * @param {string} target
     * @param {object} e
     * @param {number} datasetIndex
     */
    removeLegend: function (target, e, datasetIndex) {
        var semChart = this; // SEM.chart
        var $thisLayer = $(target).closest('.layer_chart');
        var idx = $thisLayer.data('chartIndex');
        var chartType = $thisLayer.data('chartType');
        var $thisChart = semChart.chartTempObj[idx];
        // var meta = $thisChart.getDatasetMeta(datasetIndex); // 해당 차트 라인
        var crtLineLength = $thisLayer.find('.chart_label').find('li.on').length; // 현재 show 차트 개수

        if (!$(target).closest('li').hasClass('on') || crtLineLength > 1) {
            $(target.parentNode).remove();
            $thisChart.data.datasets.splice(datasetIndex, 1, {}); // 데이터 삭제하고 데이터셋 인덱스 값 일치를 위해 빈 객체 추가
            $thisChart.update();

            if (chartType !== 'Smithchart') {
                semChart.setGridLines(idx);
                $thisChart.update();
            }
        } else {
            alert('您不能移除选中的唯一选项。');
        }

        semChart.updateSubInfo($thisLayer); // 그래프 상단 추가 정보 갱신 :: Simulation Tool
    },
    /**
     * 범례 이벤트 등록
     * @function SEM.chart.setEventLegend
     */
    setEventLegend: function (target, e, datasetIndex) {
        var semChart = this; // SEM.chart
        var $thisLayer = $(target).closest('.layer_chart');
        var idx = $thisLayer.data('chartIndex');
        var chartType = $thisLayer.data('chartType');
        var $thisChart = semChart.chartTempObj[idx];
        var meta = $thisChart.getDatasetMeta(datasetIndex); // 해당 차트 라인
        var crtLineLength = $thisLayer.find('.chart_label').find('li.on').length; // 현재 show 차트 개수
        // var lineLength = $thisChart.data.datasets.length; // 라인 개수
        // var datasets = $thisChart.config.data.datasets;

        if (meta.hidden === null) {
            // hidden
            if (crtLineLength > 1) {
                meta.hidden = true;
                $(target.parentNode).removeClass("on");
            } else {
                alert('您不能移除选中的唯一选项。');
            }
        } else {
            // show
            meta.hidden = null;
            $(target.parentNode).addClass("on");
        }

        semChart.updateSubInfo($thisLayer);  // 그래프 상단 추가 정보 갱신 :: Simulation Tool

        $thisChart.update();
        if (chartType !== 'Smithchart') {
            semChart.setGridLines(idx);
            $thisChart.update();
        }
    },
    /**
     * 범례 생성
     * @function SEM.chart.renderLegend
     */
    renderLegend: function () {
        var semChart = this;
        var chartIndex = semChart.chartTempIdx;
        var thisChart = semChart.chartTempObj[chartIndex];
        var legendHtml = thisChart.generateLegend(); // 범례 생성
        var $legendWrap = $('.layer_chart[data-chart-index="' + chartIndex + '"] .chart_label'); // 범례 삽입 대상

        $($legendWrap).append(legendHtml);
    },
    /**
     * 그리드 강조선 그리기
     * @function SEM.chart.setGridLines
     * @param {number} chartIndex 대상 차트 번호
     */
    setGridLines: function (chartIndex) {
        var semChart = this;
        var $thisChart = semChart.chartTempObj[chartIndex]; // Chart instance - 차트 생성 객체

        $thisChart.options.annotation.annotations = []; // 기존 강조선 초기화

        var xArr = $thisChart.scales['x-axis-0'].ticks.clean(''); // ticks 가져 온 후 빈 배열 제거
        var yArr = $thisChart.scales['y-axis-0'].ticks.clean(''); // ticks 가져 온 후 빈 배열 제거
        var gridValue = semChart.setAnnotation({
            x: xArr,
            y: yArr
        });

        $thisChart.options.annotation.annotations = gridValue; // 그리드 값 설정

        $thisChart.update();
    },
    /**
     * 그리드 강조선 설정
     * @function SEM.chart.setAnnotation
     * @param {object} axes x: [tick(, tick)...], y: [tick(, tick)...]
     * @return {array} 그리드 라인 위치
     */
    setAnnotation: function (axes) {
        var axesArr = [];
        var xAxes = axes.x;
        var yAxes = axes.y;

        for (var xIdx = 0; xIdx < xAxes.length; xIdx++) {
            var xTick = xAxes[xIdx];
            axesArr.push({
                drawTime: "beforeDatasetsDraw",
                type: "line",
                mode: "vertical",
                scaleID: "x-axis-0",
                value: xTick,
                borderColor: "rgba(0, 0, 0, 0.5)",
                borderWidth: 1
            });
        }

        for (var yIdx = 0; yIdx < yAxes.length; yIdx++) {
            var yTick = yAxes[yIdx];
            axesArr.push({
                drawTime: "beforeDatasetsDraw",
                type: "line",
                mode: "horizontal",
                scaleID: "y-axis-0",
                value: yTick,
                borderColor: "rgba(0, 0, 0, 0.5)",
                borderWidth: 1
            });
        }

        return axesArr;
    },
    /**
     * 차트 그리기
     * @function SEM.chart.renderChart
     * @param {string} options 차트 옵션
     * @param {string} data 차트 데이터
     * @param {string} chartType 차트 유형
     */
    renderChart: function (options, data, chartType) {
        var semChart = this; // SEM.chart
        var chartIndex = semChart.chartTempIdx;
        var target = 'myChart' + chartIndex; // 새롭게 생성된 canvas

        /* Chart.js - 차트 생성 */
        var ctx = document.getElementById(target).getContext('2d');
        var myChart = new Chart(ctx, {
            type: 'line',
            data: data,
            options: options
        });

        semChart.chartTempObj[chartIndex] = myChart; // 차트 저장

        /* 그리드 강조선 그리기 */
        if (chartType !== 'Smithchart') {
            semChart.setGridLines(chartIndex);
        }
    },
    /**
     * 레이어 재정렬
     * @function SEM.chart.arrangeLayer
     */
    arrangeLayer: function () {
        var semChart = this;
        var layer = document.querySelectorAll('.layer_chart');
        var layerLength = layer.length;
        var layerIdx = 0;
        for (var idx = 0; idx < layerLength; idx++) {
            var el = layer[idx];
            var n = idx + 1;
            el.setAttribute('data-layer-idx', n); // 위치 재설정
            layerIdx = Number(el.getAttribute('data-layer-idx')); // 위치 순서 get

            /* 위치 초기화 */
            var setOffset = semChart.setLayerPosition(layerIdx);
            el.style.top = setOffset.y + 'px';
            el.style.left = setOffset.x + 'px';

            /* z-index 초기화 */
            var zIdx = layerIdx + 1000;
            el.style.zIndex = zIdx;

            /* 크기 초기화 */
            el.style.width = '428px';
            el.style.height = '470px';

            /* 폴딩 초기화 */
            el.classList.remove('fold');
        }
    },
    /**
     * 레이어 위치 계산
     * @function SEM.chart.setLayerPosition
     * @param {number} chartLayerIdx 차트 순서
     * @return {object}
     */
    setLayerPosition: function (chartLayerIdx) {
        var num = chartLayerIdx % 6;
        var idx = 0;
        var result = {};
        var multiLineLocation = 385; // 레이어 줄 바꿈 간격
        var defaultOffset = { // 첫 시작 위치
            x: 300,
            y: 215
        };

        /* Converter Simulation Tool */
        if (document.getElementById('converterType')) {
            multiLineLocation = 265; // 레이어 줄 바꿈 간격

            defaultOffset = { // 첫 시작 위치
                x: 0,
                y: 0
            };
        }

        var layerSize = { // 레이어 크기
            w: 430,
            h: 500
        };
        var layerMargin = 5; // 레이어 간격

        // 임시 계산
        if (num === 1 || num === 4) {
            idx = 1;
        } else if (num === 2 || num === 5) {
            idx = 2;
        } else if (num === 3 || num === 0) {
            idx = 3;
        }

        result.x = layerSize.w * (idx - 1) + defaultOffset.x + layerMargin * (idx - 1);
        result.y = 215;
        result.col = idx;
        result.num = num;
        result.layerIdx = chartLayerIdx;

        /* Converter Simulation Tool */
        if (document.getElementById('converterType')) {
            result.y = 0;
        }

        if (3 < num || num === 0) {
            result.y = result.y + multiLineLocation;
        }

        return result;
    },
    /**
     * 레이어 이벤트 등록
     * @function SEM.chart.setEventLayer
     */
    setEventLayer: function () {
        var semChart = this;
        var $thisChartLayer = $('.layer_chart[data-chart-index="' + semChart.chartTempIdx + '"]'); // 해당 차트 레이어
        var $thisLayerCont = $thisChartLayer.find('.layer_cont');
        var thisChartIdx = $thisChartLayer.data('chartIndex');
        var thisChartType = $thisChartLayer.data('chartType');
        var $thisChart = semChart.chartTempObj[thisChartIdx];
        var layerIdx = semChart.chartLayerIdx;

        /* 레이어 재정렬 적용 시 */
        if ($('#toggleGraph').length) {
            var layer = document.querySelectorAll('.layer_chart');
            var layerLength = layer.length - 2;
            if (layerLength >= 0) {
                var lastLayer = layer[layerLength];
                var _idx = Number(lastLayer.getAttribute('data-layer-idx'));
                layerIdx = _idx + 1;
            }
        }

        var setOffset = semChart.setLayerPosition(layerIdx);

        $thisChartLayer.css({
            top: setOffset.y,
            left: setOffset.x
        });
        $thisChartLayer.attr('data-layer-col', setOffset.col); // 레이어 위치
        $thisChartLayer.attr('data-layer-num', setOffset.num);
        $thisChartLayer.attr('data-layer-idx', setOffset.layerIdx);

        // 레이어로 포커스 이동
        // $thisChartLayer.attr('tabIndex', '-1').focus();

        // 레이어 위치 이동
        $thisChartLayer.draggable({
            containment: '#wrap', // 레이어 이동 범위 설정
            handle: '.layer_tit',
            scroll: false
        });

        // 레이어 사이즈 조정
        $thisChartLayer.resizable({
            maxHeight: 1000,
            maxWidth: 1900,
            minHeight: 468,
            minWidth: 428,
            handles: "all"
        });

        // 레이어 리사이즈 이벤트 버블링 해제
        $thisChartLayer.resizable().on('resize', function (e) {
            e.stopPropagation();
        });

        // 레이어 폴딩
        $thisChartLayer.find('.btn_layer_fold').on('click', function () {
            if (!$thisChartLayer.hasClass('fold')) {
                $thisChartLayer.addClass('fold');
            } else {
                $thisChartLayer.removeClass('fold');
            }
        });

        // 초기 z-index 설정
        var zIdx = layerIdx + 1000;
        $thisChartLayer.css('zIndex', zIdx);

        // 레이어 최상단 노출
        $thisChartLayer.on('mousedown', function () {
            setTopZIndex();
        });

        /**
         * 레이어 최상단 노출
         */
        function setTopZIndex() {
            var _l = $('.layer_chart').length;
            var _thisZidx = $thisChartLayer.css('zIndex') * 1;
            var $el, _elZidx;
            layerIdx = semChart.chartLayerIdx - 1;

            for (var idx = 0; idx < _l; idx++) {
                $el = $('.layer_chart').eq(idx);
                _elZidx = $el.css('zIndex') * 1;

                if (_thisZidx < _elZidx) {
                    $el.css('zIndex', _elZidx - 1);
                }
            }
            $thisChartLayer.css('zIndex', layerIdx + 1000);
        }

        /* 레이어 닫기 */
        $thisChartLayer.find('.btn_layer_close').on('click', function () {
            semChart.closeLayer(thisChartIdx); // 차트 레이어 닫기
            semChart.removeChartData(thisChartIdx); // 차트 데이터 삭제
        });

        /* 설정 버튼 이벤트 등록 */
        $thisChartLayer.find('.tool_box .setting').on('click', function () {
            var axesBox = $thisChartLayer.find('.input_axes');
            if (!axesBox.hasClass('on')) {
                $thisChartLayer.find('.input_axes').addClass('on');
            } else {
                $thisChartLayer.find('.input_axes').removeClass('on');
            }
        });

        /* 차트 SParameterType 라디오버튼 이벤트 등록 */
        $thisChartLayer.find('.select_type_rd input[name^="dataType"]').on('change', function () {
            var $this = $(this);
            var type = $this.val();

            /* Y축 데이터로 차트 sort */
            semChart.sortYData(type, thisChartIdx);

            if (thisChartType !== 'Smithchart') {
                semChart.initChart(thisChartIdx);
            }
        });

        /* 차트 범위 적용 버튼 이벤트 등록 */
        $thisChartLayer.find('.btn_apply').on('click', function () {
            var axes = $(this).data('axes');
            var min, max, minValue, maxValue;
            var range = {};

            min = 'input' + axes.toUpperCase() + 'Min' + thisChartIdx; // 가져올 대상
            max = 'input' + axes.toUpperCase() + 'Max' + thisChartIdx; // 가져올 대상
            minValue = document.getElementById(min).value; // 가져올 값
            maxValue = document.getElementById(max).value; // 가져올 값

            if (minValue !== '') {
                range.min = minValue * 1;
            }
            if (maxValue !== '') {
                range.max = maxValue * 1;
            }

            var axesType = $thisChartLayer.find('input[name^=chart' + axes.toUpperCase() + ']:checked').val();

            semChart.setRangeAxes(thisChartIdx, axes, axesType, range);
        });

        /* 차트 축 유형 변환 이벤트 등록 */
        $thisChartLayer.find('[name^="chart"]').on('change', function () {
            var $this = $(this);
            var options = {}; // 변환에 필요한 정보

            options.axes = $this.closest('.select_type').data('chartAxes');
            options.axesType = $this.val();
            options.chartType = thisChartType;
            options.chartIndex = thisChartIdx;

            semChart.setAxesType(options);
        });

        /* 축 범위 문자 입력 방지 */
        $thisChartLayer.find('.input_axes input[type=text]').on('input', function () {
            this.value = this.value.replace(/[^0-9.-]/g, '').replace(/(\-.*)\-/g, '$1').replace(/(\..*)\./g, '$1');
        });

        /* 차트 초기화 버튼 이벤트 등록 - 현재 차트 유형으로 차트 유형 변환 함수 실행 */
        $thisChartLayer.find('.btn_reset').on('click', function () {
            var $this = $(this);
            var options = {}; // 초기화에 필요한 정보

            options.axes = $this.data('axes');
            options.axesType = $this.parent().parent().find('[name^="chart"]:checked').val();
            options.chartType = thisChartType;
            options.chartIndex = thisChartIdx;

            // scales.ticks 만 초기화가 되는지 확인
            semChart.setAxesType(options); // 차트 유형 변환 === 차트 초기화
        });
    },
    /**
     * 해당하는 차트 데이터 삭제
     * @param {number} chartIdx 지정할 차트 번호
     */
    removeChartData: function (chartIdx) {
        var semChart = SEM.chart;

        semChart.chartTempObj[chartIdx].destroy();
        delete semChart.chartTempObj[chartIdx]; // 해당 객체 삭제
        delete semChart.chartOriginData[chartIdx]; // 해당 객체 삭제
    },
    /**
     * 해당하는 차트 레이어 닫기
     * @param {number} chartIdx 지정할 차트 번호
     */
    closeLayer: function (chartIdx) {
        var semChart = this;
        var $thisChartLayer = $('.layer_chart[data-chart-index="' + chartIdx + '"]'); // 해당 차트 레이어

        $thisChartLayer.remove();

        var size = document.querySelectorAll('.layer_chart').length;

        // 노출된 레이어가 없을 때 레이어 위치 초기화
        if (size === 0) {
            semChart.chartLayerIdx = 1;

            if ($('#toggleGraph').length) {
                $('#toggleGraph').prop('checked', false); // 차트 토글 버튼 off
            }
        }
    },
    /**
     * 레이어 요소 생성
     * @function SEM.chart.renderLayer
     * @param {string} chartType 차트 유형
     * @return {number} layerIdx 최근에 생성된 layer_chart 팝업 index 값
     */
    renderLayer: function (chartType) {
        var semChart = this; // SEM.chart
        var target = $('#wrap'); // 렌더링 위치
        /* Converter Simulation Tool */
        if (document.getElementById('converterType')) {
            target = $('#contentWrap'); // 렌더링 위치
        }
        var thisIndex = semChart.chartTempIdx; // 해당 차트 번호
        var chartInfo = semChart.getTypeInfo(chartType); // 차트 유형 정보
        if (!chartInfo) return false; // 설정 파일에 해당 차트 유형이 없을 경우
        var xAxesType = chartInfo.axesType.x;
        var yAxesType = chartInfo.axesType.y;
        var selectDataType = []; // 데이터 선택 라디오 버튼 레이아웃
        var toolBox = []; // 도구 모음 레이아웃
        var layerChart = []; // 차트 전체 레이아웃
        var layerInput = []; // 차트 옵션 조정 레이아웃

        // 데이터 선택 라디오 버튼
        if (chartInfo.hasOwnProperty('selectYData')) {
            var selectYData = chartInfo.selectYData();
            var yType = selectYData.type;
            var display = selectYData.display;

            if (display) {
                selectDataType.push('<div class="select_type_rd">');
                selectDataType.push('    <ul>');
                for (var idx = 0; idx < yType.length; idx++) {
                    var yTypeOrigin = yType[idx]; // 원본 구분값 DeltaC, DeltaT
                    var yTypeSting = yTypeOrigin; // front 표현 값 ΔC, ΔT

                    if (yTypeOrigin === 'DeltaC') {
                        yTypeSting = 'ΔC';
                    } else if (yTypeOrigin === 'DeltaT') {
                        yTypeSting = 'ΔT';
                    }

                    selectDataType.push('        <li>');
                    selectDataType.push('            <input type="radio" name="dataType' + thisIndex + '" id="dataType' + thisIndex + yTypeSting + '" value="' + yTypeOrigin + '">');
                    selectDataType.push('            <label name="dataType' + thisIndex + '" for="dataType' + thisIndex + yTypeSting + '">' + yTypeSting + '</label>');
                    selectDataType.push('        </li>');
                }
                selectDataType.push('    </ul>');
                selectDataType.push('</div>');
                selectDataType = selectDataType.join('\n');
            }
        }

        // 차트 옵션 조정
        if (chartType !== 'Smithchart' && chartType !== 'AppliedVI') {
            layerInput.push('<div class="input_axes">');
            layerInput.push('	<div class="x_axes">');
            layerInput.push('		<div class="tit_axes">X轴</div>');
            layerInput.push('		<div class="cont_axes">');
            layerInput.push('   		<div class="select_type" data-chart-axes="x">');
            layerInput.push('   		    <ul>');
            if (xAxesType === 'linear') {
                layerInput.push('   		        <li>');
                layerInput.push('   			        <input class="rd" type="radio" name="chartX' + thisIndex + '" id="chartXLinear' + thisIndex + '" value="linear" checked>');
                layerInput.push('   			        <label class="label" for="chartXLinear' + thisIndex + '">Linear</label>');
                layerInput.push('   		        </li>');
                layerInput.push('   		        <li>');
                layerInput.push('   			        <input class="rd" type="radio" name="chartX' + thisIndex + '" id="chartXLog' + thisIndex + '" value="logarithmic">');
                layerInput.push('   			        <label class="label" for="chartXLog' + thisIndex + '">Log</label>');
                layerInput.push('   		        </li>');
            } else if (xAxesType === 'logarithmic') {
                layerInput.push('   		        <li>');
                layerInput.push('   			        <input class="rd" type="radio" name="chartX' + thisIndex + '" id="chartXLinear' + thisIndex + '" value="linear">');
                layerInput.push('   			        <label class="label" for="chartXLinear' + thisIndex + '">Linear</label>');
                layerInput.push('   		        </li>');
                layerInput.push('   		        <li>');
                layerInput.push('   			        <input class="rd" type="radio" name="chartX' + thisIndex + '" id="chartXLog' + thisIndex + '" value="logarithmic" checked>');
                layerInput.push('   			        <label class="label" for="chartXLog' + thisIndex + '">Log</label>');
                layerInput.push('   		        </li>');
            }
            layerInput.push('   		    </ul>');
            layerInput.push('   		</div>');
            layerInput.push('   		<div class="input_box_wrap">');
            layerInput.push('   		    <div class="input_box">');
            layerInput.push('   		    	<span class="label_box"><label class="tit" for="inputXMin' + thisIndex + '">最低</label></span>');
            layerInput.push('   		    	<input type="text" id="inputXMin' + thisIndex + '">');
            layerInput.push('   		    </div>');
            layerInput.push('   		    <div class="input_box">');
            layerInput.push('   		    	<span class="label_box"><label class="tit" for="inputXMax' + thisIndex + '">最大</label></span>');
            layerInput.push('   		    	<input type="text" id="inputXMax' + thisIndex + '">');
            layerInput.push('   		    </div>');
            layerInput.push('   		</div>');
            layerInput.push('   		<div class="btn_wrap">');
            layerInput.push('   			<button type="button" class="btn_apply" data-axes="x">应用</button>');
            layerInput.push('   			<button type="button" class="btn_reset" data-axes="x">重置</button>');
            layerInput.push('   		</div>'); // btn_wrap
            layerInput.push('		</div>'); // cont_axes
            layerInput.push('	</div>'); // x_axes
            layerInput.push('	<div class="y_axes">');
            layerInput.push('		<div class="tit_axes">Y轴</div>');
            layerInput.push('		<div class="cont_axes">');
            layerInput.push('		    <div class="select_type" data-chart-axes="y">');
            layerInput.push('   		    <ul>');
            if (yAxesType === 'linear') {
                layerInput.push('               <li>');
                layerInput.push('			        <input class="rd" type="radio" name="chartY' + thisIndex + '" id="chartYLinear' + thisIndex + '" value="linear" checked>');
                layerInput.push('			        <label class="label" for="chartYLinear' + thisIndex + '">Linear</label>');
                layerInput.push('		        </li>');
                layerInput.push('		        <li>');
                layerInput.push('			        <input class="rd" type="radio" name="chartY' + thisIndex + '" id="chartYLog' + thisIndex + '" value="logarithmic">');
                layerInput.push('			        <label class="label" for="chartYLog' + thisIndex + '">Log</label>');
                layerInput.push('		        </li>');
            } else if (yAxesType === 'logarithmic') {
                layerInput.push('               <li>');
                layerInput.push('			        <input class="rd" type="radio" name="chartY' + thisIndex + '" id="chartYLinear' + thisIndex + '" value="linear">');
                layerInput.push('			        <label class="label" for="chartYLinear' + thisIndex + '">Linear</label>');
                layerInput.push('		        </li>');
                layerInput.push('		        <li>');
                layerInput.push('			        <input class="rd" type="radio" name="chartY' + thisIndex + '" id="chartYLog' + thisIndex + '" value="logarithmic" checked>');
                layerInput.push('			        <label class="label" for="chartYLog' + thisIndex + '">Log</label>');
                layerInput.push('		        </li>');
            }
            layerInput.push('   		    </ul>');
            layerInput.push('   		</div>'); // select_type
            layerInput.push('   		<div class="input_box_wrap">');
            layerInput.push('   		    <div class="input_box">');
            layerInput.push('   		    	<span class="label_box"><label class="tit" for="inputYMin' + thisIndex + '">最低</label></span>');
            layerInput.push('   		    	<input type="text" id="inputYMin' + thisIndex + '">');
            layerInput.push('   		    </div>');
            layerInput.push('   		    <div class="input_box">');
            layerInput.push('   		    	<span class="label_box"><label class="tit" for="inputYMax' + thisIndex + '">最大</label></span>');
            layerInput.push('   		    	<input type="text" id="inputYMax' + thisIndex + '">');
            layerInput.push('   		    </div>');
            layerInput.push('   		</div>'); // input_box_wrap
            layerInput.push('   		<div class="btn_wrap">');
            layerInput.push('   			<button type="button" class="btn_apply" data-axes="y">应用</button>');
            layerInput.push('   			<button type="button" class="btn_reset" data-axes="y">重置</button>');
            layerInput.push('   		</div>'); // btn_wrap
            layerInput.push('		</div>'); // cont_axes
            layerInput.push('	</div>'); // y_axes
            layerInput.push('</div>'); // input_axes
            layerInput = layerInput.join('\n');
        }

        // 도구 모음
        toolBox.push('<div class="tool_box">');

        if (chartInfo.hasOwnProperty('viewSubInfo')) {
            var viewSubInfo = chartInfo.viewSubInfo();
            toolBox.push('    <div class="sub_info" style="color: rgb(237, 27, 36);">');
            toolBox.push('          ' + viewSubInfo.title + ': <span class="val"></span>' + viewSubInfo.unit);
            toolBox.push('    </div>');
        }

        toolBox.push('    <div class="left_wrap">');
        toolBox.push('        <button type="button" class="btn download" onclick="SEM.chart.saveData(this); ' + "gtag('event', 'graphfn_datadown', {'event_category':'GRAPH', 'event_label':'SEM_CL_W_CN'});" + '">다운로드</button>');
        toolBox.push('        <button type="button" class="btn save_img" onclick="SEM.chart.downloadImg(this); ' + "gtag('event', 'graphfn_imgdown', {'event_category':'GRAPH', 'event_label':'SEM_CL_W_CN'});" + '">이미지 저장</button>');
        toolBox.push('        <button type="button" class="btn print" onclick="SEM.chart.printLayer(this); ' + "gtag('event', 'graphfn_print', {'event_category':'GRAPH', 'event_label':'SEM_CL_W_CN'});" + '">프린트</button>');
        toolBox.push('    </div>');
        if (chartType !== 'Smithchart' && chartType !== 'AppliedVI') {
            toolBox.push('    <div class="right_wrap">');
            toolBox.push('        <button type="button" class="btn setting layer_tool_setting">설정</button>');
            toolBox.push('    </div>');
            toolBox.push(layerInput);
        }
        toolBox.push('</div>');
        toolBox = toolBox.join('\n');

        // 차트 전체 레이아웃
        layerChart.push('<div class="layer_chart" id="layerChart' + thisIndex + '" data-chart-index="' + thisIndex + '" data-chart-type="' + chartType + '">');
        layerChart.push('	<div class="layer_tit" id="layerChart' + thisIndex + 'header" style="background-color:' + chartInfo.layerTitle.backgroundColor + '">');
        layerChart.push('	    <span class="txt">' + chartInfo.layerTitle.title() + '</span>');
        layerChart.push('	</div>');
        layerChart.push('   <div class="layer_cont">');
        layerChart.push('       <div class="layer_cont_inner">');
        if (chartInfo.hasOwnProperty('selectYData')) {
            layerChart.push(selectDataType);
        }
        layerChart.push(toolBox);
        layerChart.push('           <div class="canvas_wrap">');
        if (chartType === 'Smithchart') {
            layerChart.push('               <canvas id="myChart' + thisIndex + '" class="smith_canvas" width="280" height="280"></canvas>');
        } else {
            layerChart.push('               <canvas id="myChart' + thisIndex + '" width="380" height="266"></canvas>');
        }
        layerChart.push('           </div>');
        layerChart.push('	        <div class="chart_label"></div>');
        layerChart.push('       </div>');
        layerChart.push('   </div>');
        layerChart.push('   <button type="button" class="btn_layer_fold">레이어 접기</button>');
        layerChart.push('   <button type="button" class="btn_layer_close">레이어 닫기</button>');
        layerChart.push('</div>');
        layerChart = layerChart.join('\n');
        target.append(layerChart);

        return true;
    },
    /**
     * 데이터 셋 생성
     * @function SEM.chart.setDataset
     * @return 데이터 셋을 포함한 object
     */
    setDataset: function () {
        var semChart = this;
        var data = {
            datasets: []
        };
        var originData = semChart.chartOriginData[semChart.chartTempIdx];
        var gT = originData.graphType;
        var partsArr = originData.selectPartsList; // 받아온 파트 목록 최대 6개
        var lineIdx = 0; // 차트 라인 구분용 인덱싱
        var modelTypeLeng = originData.selectPartsList[0].chartList.length;
        var standardType = false;
        var standardPartsName = false;

        // Simulation Tool
        if (originData.hasOwnProperty('standardType')) {
            standardType = originData.standardType;
        }
        if (originData.hasOwnProperty('standardPartsName')) {
            standardPartsName = originData.standardPartsName;
        }

        for (var i = 0; i < partsArr.length; i++) {
            var currentPart = partsArr[i]; // 해당 파트
            var chartArr = currentPart.chartList; // 해당 파트의 차트 data정보 배열
            for (var j = 0; j < chartArr.length; j++) {
                var tempDataset = chartArr[j];

                tempDataset.label = currentPart.partsName;
                tempDataset.borderColor = semChart.chartColors[lineIdx];
                tempDataset.pointBackgroundColor = 'rgba(255, 255, 255, 0)'; // 투명
                tempDataset.pointBorderColor = 'rgba(255, 255, 255, 0)'; // 투명
                tempDataset.borderWidth = 1.5;
                tempDataset.fill = false; // 그래프 배경 채우기
                tempDataset.pointHitRadius = 5; // 툴팁 활성화 hover 범위

                //y축 멀티
                if(gT == "AppliedVI"){
                    if(tempDataset.graphSubType == "AppliedV"){
                        tempDataset.yAxisID = 'y-axis-0';
                    }else if(tempDataset.graphSubType == "AppliedI"){
                        tempDataset.yAxisID = 'y-axis-1';
                    };
                };

                // Simulation Tool
                if (standardType) {
                    tempDataset.standardType = standardType;
                }
                if (standardPartsName) {
                    tempDataset.standardPartsName = standardPartsName;
                }

                // dataset에 필요한 정보 밀어 넣기
                for (var key in currentPart) {
                    if (currentPart.hasOwnProperty(key) && key !== 'chartList') {
                        tempDataset[key] = currentPart[key];
                    }
                }

                data.datasets.push(tempDataset);
                if (gT === 'RippleCurr' || gT === 'TCC' || gT === 'DCBiasByTemp' || gT === 'TCCbyDC' || gT === 'DCBias' || gT === 'ACVolt' || gT === 'Smithchart') {
                    // 차트 라인 색상 그룹화
                    if (j % 2 !== 0) {
                        lineIdx++;
                    }
                } else if (gT === 'SDB') {
                    if (modelTypeLeng / 4 === 1) {
                        //모델모드가 1개일때
                        if (j === chartArr.length - 1) {
                            lineIdx++;
                        }
                    } else if (modelTypeLeng / 4 === 2) {
                        //모델모드가 2개일때
                        if (j === (chartArr.length / 2) - 1 || j === chartArr.length - 1) {
                            lineIdx++;
                        }
                    }
                } else {
                    // 일반 차트
                    lineIdx++;
                }
            }
        }

        return data;
    },
    /**
     * 로그 변환
     * @function SEM.chart.convertLogAxes
     * @param {number} value 원본 데이터 최대, 최소 설정 값
     * @param {number} rangeD min, max
     * @return {number} 로그로 변환 된 값
     */
    convertLogAxes: function (value, rangeD) {
        var result;
        if (rangeD === 'max') {
            result = Math.pow(10, Math.ceil(Math.log(value) * Math.LOG10E));
            if (isNaN(result)) { // 로그 값이 음수일 때
                result = 100;
            }
        } else if (rangeD === 'min') {
            result = Math.pow(10, Math.floor(Math.log(value) * Math.LOG10E));
            if (isNaN(result)) { // 로그 값이 음수일 때
                result = 0;
            }
        }
        return result;
    },
    /**
     * 차트 유형에 해당하는 정보 가져오기
     * @param {string} chartType 차트 유형
     * @return 차트 유형 정보(축 유형, 축 라벨스트링 정보)
     */
    getTypeInfo: function (chartType) {
        var semChart = this;
        var chartInfo = semChart.chartTypeInfo[chartType];

        if (chartInfo) {
            return chartInfo;
        } else {
            semChart.isRun = false; // 차트 실행 가능으로 변경
            SEM.console.log('차트 세팅 옵션에 해당하는 차트 유형이 설정되어 있지 않습니다.');
        }
    },
    /**
     * 차트 축 범위 설정
     * @function SEM.chart.setRangeAxes
     * @param {number} chartIndex 차트 번호
     * @param {string} axes 축
     * @param {object} range 범위(최대, 최소)
     */
    setRangeAxes: function (chartIndex, axes, axesType, range) {
        var semChart = this; // SEM.chart
        var $thisChart = semChart.chartTempObj[chartIndex];

        if (range.hasOwnProperty('max') && axesType === 'logarithmic') {
            range.max = semChart.convertLogAxes(range.max, 'max');
        }

        if (range.hasOwnProperty('min') && axesType === 'logarithmic') {
            range.min = semChart.convertLogAxes(range.min, 'min');
        }

        if (axes === 'x') {
            if (range.hasOwnProperty('min')) {
                $thisChart.options.scales.xAxes[0].ticks.min = range.min;
            }
            if (range.hasOwnProperty('max')) {
                $thisChart.options.scales.xAxes[0].ticks.max = range.max;
            }
        } else if (axes === 'y') {
            if (range.hasOwnProperty('min')) {
                $thisChart.options.scales.yAxes[0].ticks.min = range.min;
            }
            if (range.hasOwnProperty('max')) {
                $thisChart.options.scales.yAxes[0].ticks.max = range.max;
            }
        }

        $thisChart.update();

        /* 그리드 강조선 그리기 */
        semChart.setGridLines(chartIndex);
    },
    /**
     * 차트 축 유형 변환
     * @function SEM.chart.setAxesType
     * @param {object} options 변환에 필요한 정보 // axes, axesType, chartType, chartIndex
     */
    setAxesType: function (options) {
        var semChart = this; // SEM.chart
        var axes = options.axes; // 축
        var axesType = options.axesType; // 축 유형
        var chartType = options.chartType; // 차트 유형
        var chartIndex = options.chartIndex; // 차트 번호
        var $thisChart = semChart.chartTempObj[chartIndex]; // 해당 차트
        var $thisChartLayer = $('.layer_chart[data-chart-index="' + chartIndex + '"]'); // 해당 차트 레이어
        var scaleOptions = semChart.setAxesOptions(axes, axesType, chartType, chartIndex); // 축 옵션 설정

        // 덮어씌워짐, 병합 대상 설정 다시 보기
        $thisChart.options.scales[axes + 'Axes'] = Chart.helpers.scaleMerge(semChart.chartOptions.scales, {
            option: [scaleOptions]
        }).option;

        $thisChart.update();

        /* 그리드 강조선 그리기 */
        if (chartType !== 'Smithchart') {
            semChart.setGridLines(chartIndex);
        }

        /* 범위 인풋 값 비워주기 */
        if (axes === 'x') {
            $thisChartLayer.find('.x_axes input[type="text"]').val('');
        } else if (axes === 'y') {
            $thisChartLayer.find('.y_axes input[type="text"]').val('');
        }
    },
    /**
     * 차트 축 옵션 설정
     * @function SEM.chart.setAxesOptions
     * @param {string} axes 설정할 대상 축 - x, y
     * @param {string} axesType 설정할 축의 타입 - linear, logarithmic
     * @param {string} chartType 설정할 차트 타입 - |Z|, R, LCurrent ...
     * @param {number} chartIndex 설정할 대상
     * @return {object} 설정 축과 타입에 해당하는 옵션 값
     */
    setAxesOptions: function (axes, axesType, chartType, chartIndex) {
        var semChart = this;
        var scaleOptionsArr = [];
        var scaleOptions = {};
        var typeInfo = semChart.getTypeInfo(chartType); // 선택된 차트 기본 설정 정보 저장
        var thisLayerData = semChart.chartOriginData[chartIndex]; // 해당 차트 원본 데이터
        var $thisChartLayer = $('.layer_chart[data-chart-index="' + chartIndex + '"]'); // 해당 차트 레이어
        var labelTitle = '';
        var yData = $thisChartLayer.find('.select_type_rd input[name^="dataType"]:checked').val() || (typeInfo.hasOwnProperty('selectYData') ? typeInfo.selectYData().type[0] : null); // y축 셀렉트 가능 할 때

        if (axesType === 'linear') {
            scaleOptions = {
                type: 'linear', // 축 타입
                ticks: {
                    userCallback: function (tick, index, ticks) {
                        var intervalCurrent = 0;
                        var currentTick = ticks[index];
                        var intervalTicks = Math.abs(fixCalc(ticks[1] - ticks[2])); // 최근 표현된 축의 간격(stepSize) - 축의 간격 구하는 방법이 있는지 알아보기(라이브러리도 이런식으로 계산 2018-11-29 확인됨)

                        /* 부동 소수점 계산 오류 정정 */
                        function fixCalc(value) {
                            return Number(value.toFixed(11));
                        }

                        /**
                         * min, max 지정시 표현된 축의 stepSize보다 간격이 좁을 경우 해당 설정 tick 생략
                         * x는 오름차순
                         * y는 내림차순
                         */
                        if (axes === 'x') {
                            // min
                            if (index === 0) {
                                intervalCurrent = Math.abs(fixCalc(currentTick - ticks[index + 1]));

                                if (intervalCurrent !== intervalTicks) {
                                    return '';
                                }
                            }
                            // max
                            if (index === ticks.length - 1) {
                                intervalCurrent = Math.abs(fixCalc(currentTick - ticks[index - 1]));

                                if (intervalCurrent !== intervalTicks) {
                                    return '';
                                }
                            }
                        } else if (axes === 'y') {
                            // min
                            if (index === ticks.length - 1) {
                                intervalCurrent = Math.abs(fixCalc(currentTick - ticks[index - 1]));

                                if (intervalCurrent !== intervalTicks) {
                                    return '';
                                }
                            }
                            // max
                            if (index === 0) {
                                intervalCurrent = Math.abs(fixCalc(currentTick - ticks[index + 1]));

                                if (intervalCurrent !== intervalTicks) {
                                    return '';
                                }
                            }
                        }

                        tick = fixCalc(tick);
                        return tick;
                    }
                }
            };
        } else if (axesType === 'logarithmic') {
            scaleOptions = {
                type: 'logarithmic', // 축 타입
                ticks: {
                    max: semChart.convertLogAxes(thisLayerData.maximum[axes], 'max'), // 축 최대 범위 설정
                    maxRotation: 0, // 축 tick 최대 기울기
                    userCallback: function (tick, index, ticks) {
                        tick = fixCalc(tick); // 부동 소수점 오류 정정
                        var remain = tick / fixCalc(Math.pow(10, Math.floor(Chart.helpers.log10(tick)))); // 로그 계산
                        remain = fixCalc(remain); // 부동 소수점 오류 정정
                        var exponential = false; // 지수 표현 기준

                        // IE Polyfill
                        if (Number.parseFloat === undefined) {
                            Number.parseFloat = parseFloat;
                        }

                        /* 부동 소수점 계산 오류 정정 */
                        function fixCalc(value) {
                            return Number(value.toFixed(11));
                        }

                        // 축에 지수 표현이 필요할 때
                        if (typeInfo.hasOwnProperty('axesExponential')) {
                            exponential = typeInfo.axesExponential;
                        }
                        if (exponential) {
                            if (exponential.x && axes === 'x') { // x축이 true 일 때
                                if (tick === 0) {
                                    return '0';
                                } else if (remain === 1) { // 1에 해당하는 것만 축에 표현
                                    tick = Number.parseFloat(tick).toExponential();

                                    return tick.toString();
                                }
                                return '';
                            }

                            if (exponential.y && axes === 'y') { // y축이 true 일 때
                                if (tick === 0) {
                                    return '0';
                                } else if (remain === 1) { // 1에 해당하는 것만 축에 표현
                                    tick = Number.parseFloat(tick).toExponential();
                                    return tick.toString();
                                }
                                return '';
                            }
                        }

                        // log tick 10개 이상 일 때 적용
                        if (ticks.length > 80) {
                            if (tick === 0) {
                                return '0';
                            } else if (remain === 1 && Math.floor(Chart.helpers.log10(tick)) % 2 === 0) { // tick의 개수가 10개 이상일 때에는 1/2만 표현
                                return tick.toString();
                            }
                            return '';
                        }

                        if (tick === 0) {
                            return '0';
                        } else if (remain === 1) { // 1에 해당하는 것만 축에 표현
                            return tick.toString();
                        }

                        return '';
                    }
                }
            };
        }

        scaleOptions.ticks.fontSize = 12;
        scaleOptions.ticks.autoSkip = false;
        scaleOptions.ticks.padding = 10;
        // scaleOptions.ticks.maxTicksLimit = 4; // tick 최대 개수

        if (axes === 'y' && typeInfo.hasOwnProperty('selectYData')) {
            labelTitle = typeInfo.selectYData().title[yData]; // y축 타이틀 y축 DATA 에 맞춰서 설정
        } else {
            labelTitle = typeInfo.label[axes];
        }
        scaleOptions.scaleLabel = {
            display: true,
            labelString: labelTitle
        };
        scaleOptions.gridLines = {
            drawTicks: false
        };

        // 축 범위 설정
        if (typeInfo.hasOwnProperty('axesRange')) {
            var infoRange = typeInfo.axesRange(yData, thisLayerData.maximum);

            if (infoRange[axes]) {
                if (infoRange[axes].hasOwnProperty('min')) {
                    scaleOptions.ticks.min = infoRange[axes].min;
                }
                if (infoRange[axes].hasOwnProperty('max')) {
                    scaleOptions.ticks.max = infoRange[axes].max;
                }
                if (infoRange[axes].hasOwnProperty('stepSize')) {
                    scaleOptions.ticks.stepSize = infoRange[axes].stepSize;
                }
            }
        };

        if (chartType === 'Smithchart') {
            scaleOptions = {
                type: axesType, // 축 타입
                display: false,
                gridLines: {
                    display: false
                },
                ticks: {
                    min: -1,
                    max: 1
                }

            };
        };


        //y축 multi[241022]
        if(axes === 'y' && typeInfo.hasOwnProperty('axesPosition')){
            var axisLeng = thisLayerData.selectPartsList[0].chartList.length;

            for(var i = 0; i < axisLeng; i++){
                var obj = $.extend(true, {}, scaleOptions);
                var target = thisLayerData.selectPartsList[0].chartList[i];
                var graphSubType = target.graphSubType;
                var infoPos = typeInfo.axesPosition(graphSubType);

                if (infoPos[axes]){
                    if (infoPos[axes].hasOwnProperty('min')) {
                        obj.ticks.min = infoPos[axes].min;
                    };
                    if (infoPos[axes].hasOwnProperty('max')) {
                        obj.ticks.max = infoPos[axes].max;
                    };
                    if (infoPos[axes].hasOwnProperty('pos')) {
                        obj['id'] = 'y-axis-'+ i;
                        obj['position'] = infoPos[axes].pos;
                    };
                    if (infoPos[axes].hasOwnProperty('label')) {
                        obj.scaleLabel.labelString = infoPos[axes].label;
                    };
                };
                scaleOptionsArr.push(obj);
            };
        }else{
            scaleOptionsArr.push(scaleOptions);
        };

        return scaleOptionsArr;
    },
    /**
     * 초기 옵션 설정
     * @function SEM.chart.initOptions
     * @param {string} chartType 차트 유형
     * @return {object} 초기 옵션값
     */
    initOptions: function (chartType) {
        var semChart = this; // SEM.chart
        var chartIndex = semChart.chartTempIdx;
        var tempOptions = $.extend(true, {}, semChart.chartOptions); // 기본 옵션 복사, 차트 초기 실행에만 사용
        var typeInfo = semChart.getTypeInfo(chartType); // 선택된 차트 기본 설정 정보 저장

        if (chartType === 'Smithchart') {
            tempOptions.onResize = null;
            tempOptions.maintainAspectRatio = true;
        }

        var xAxes = semChart.setAxesOptions('x', typeInfo.axesType.x, chartType, chartIndex); // x축 옵션 정보
        var yAxes = semChart.setAxesOptions('y', typeInfo.axesType.y, chartType, chartIndex); // y축 옵션 정보

        for(var i = 0 ; i < xAxes.length; i++){
            if(i > 0){
                tempOptions.scales.xAxes.push(xAxes[i]);
            }else{
                $.extend(tempOptions.scales.xAxes[i], xAxes[i]); // 옵션 복사본에 병합    
            };
        };
        for(var i = 0 ; i < yAxes.length; i++){
            if(i > 0){
                tempOptions.scales.yAxes.push(yAxes[i]);
            }else{
                $.extend(tempOptions.scales.yAxes[i], yAxes[i]); // 옵션 복사본에 병합
            }
            $.extend(tempOptions.scales.yAxes[i], yAxes[i]); // 옵션 복사본에 병합
        };
        // $.extend(tempOptions.scales.xAxes[0], xAxes); // 옵션 복사본에 병합
        // $.extend(tempOptions.scales.yAxes[0], yAxes); // 옵션 복사본에 병합

        // 툴팁 설정
        if (typeInfo.hasOwnProperty('tooltipLabel')) {
            tempOptions.tooltips.callbacks.label = typeInfo.tooltipLabel;
        }

        // 범례 설정
        if (typeInfo.hasOwnProperty('legendCallback')) {
            tempOptions.legendCallback = typeInfo.legendCallback;
        }

        return tempOptions;
    },
    setLazyLoad: function () {
        var semChart = this;
        var $thisChartLayer = $('.layer_chart[data-chart-index="' + semChart.chartTempIdx + '"]'); // 해당 차트 레이어
        var $thisLayerCont = $thisChartLayer.find('.layer_cont');
        var thisChartIdx = $thisChartLayer.data('chartIndex');
        var thisChartType = $thisChartLayer.data('chartType');

        var loaderNode = '<div class="layer_loader"></div>';
        $thisLayerCont.append(loaderNode);
        var $loader = $thisLayerCont.find('.layer_loader');

        $loader.jqxLoader({
            text: "",
            width: 'auto',
            height: 'auto',
            autoOpen: true
        });
    },
    /**
     * 데이터 받아온 후 처리
     * @function SEM.chart.afterGetData
     * @param {string} chartType 받아온 데이터에서 가져온 차트 유형
     */
    afterGetData: function (chartType) {
        var semChart = this;
        var initOptions = semChart.initOptions(chartType); // 시작 옵션 설정
        var dataset = semChart.setDataset(); // 차트 데이터
        var typeInfo = semChart.getTypeInfo(chartType); // 옵션 설정 값

        semChart.renderChart(initOptions, dataset, chartType); // 차트 생성
        semChart.renderLegend(); // 범주 생성

        // Y축 데이터 sort
        var _t = 'layerChart' + semChart.chartTempIdx;
        var _el = document.getElementById(_t);
        if (typeInfo.hasOwnProperty('selectYData')) {
            var selectYData = typeInfo.selectYData();
            var display = typeInfo.selectYData().display;

            semChart.sortYData(selectYData.type[0], semChart.chartTempIdx); //chart_setting_xxxx.js 의 selectYData.type[0] 값으로 default 설정 :: 2020-03-25 주석만 추가

            if (display) {
                _el.querySelector('.select_type_rd input[type="radio"]').checked = true; // 라디오 버튼 활성화
            }
        }

        // 추가 정보 표시 :: Simulation Tool
        if (typeInfo.hasOwnProperty('viewSubInfo')) {
            var subInfo = typeInfo.viewSubInfo();
            var _key = subInfo.key;
            var _value;

            if (_key === 'DUTY') {
                _value = Number(dataset.datasets[0][_key]) * 100;
                _value = _value.toFixed(2) * 1;
                _value = _value === 0 ? 0 : _value;
            } else if (_key === 'IMAX') {
                _value = Number(dataset.datasets[0][_key]).toFixed(2) * 1;
            } else if (_key === 'VPP') {
                _value = Number(dataset.datasets[0][_key]).toFixed(5) * 1000;
            }

            _el.querySelector('.sub_info .val').innerText = _value;
        }

        semChart.chartTempIdx++; // 차트 인덱싱 갱신

        $(_el).find('.layer_loader').remove();

        semChart.chartLayerIdx++; // 차트 레이어 위치 갱신
        semChart.isRun = false; // 차트 실행 가능으로 변경
    },
    /**
     * 빈 체크박스 방지
     * @method SEM.chart.preventUnChecked
     * @param {string} name 대상 name 값
     */
    preventUnChecked: function (name) {
        var element, _target = document.querySelectorAll('[name^="' + name + '"]');
        for (var i = 0; i < _target.length; i++) {
            element = _target[i];
            element.addEventListener('change', checkedSize);
        }

        function checkedSize() {
            var el, chked = 0;

            // 체크된 개수
            for (var j = 0; j < _target.length; j++) {
                el = _target[j];

                if (el.checked) {
                    chked++;
                }
            }
            if (!chked) {
                this.checked = true;
                alert('您不能移除选中的唯一选项。');
            }
        }
    },
    /** 파트 목록 정보 가져오기
     * @function SEM.chart.getInfoPartList
     * @param {string} selectedPartId 파트 목록 대상 ID
     * @return {object} 선택된 파트 목록 정보
     */
    getInfoPartList: function (selectedPartId) {
        var selectedPart = document.getElementById(selectedPartId); // 선택된 파트
        var _e, _className, list, infoPartList = [],
            paramList = {};
        if (selectedPart !== null) {
            list = selectedPart.querySelectorAll('li');

            for (var idx = 0; idx < list.length; idx++) {
                _e = list[idx];
                _classList = _e.classList;

                for (var cIdx = 0; cIdx < _classList.length; cIdx++) {
                    _className = _classList[cIdx];

                    if (_className === 'on') { // 선택된 것만 저장

                        if (_e.getAttribute('data-request') !== 'false') { // Simulation 경고 팝업 뜰 때는 전송하지 않음
                            paramList = {};
                            if (_e.querySelector('[name="partsChk"]')) {
                                paramList.partsName = _e.querySelector('[name="partsChk"]').value;
                            }
                            if (_e.querySelector('[name="paramList[][vdc]"]')) {
                                paramList.vdc = _e.querySelector('[name="paramList[][vdc]"]').value;
                            }
                            if (_e.querySelector('[name="paramList[][adc]"]')) {
                                paramList.adc = _e.querySelector('[name="paramList[][adc]"]').value;
                            }
                            if (_e.querySelector('[name="paramList[][degC]"]')) {
                                paramList.degC = _e.querySelector('[name="paramList[][degC]"]').value;
                            }
                            if (_e.querySelector('[name="ratedVdc"]')) { // MLCC>A/N
                                paramList.ratedVdc = _e.querySelector('[name="ratedVdc"]').value;
                            }
                            if (_e.querySelector('[name="capacitorList[][pcs]"]')) { // Converter Simulation Tool
                                paramList.capCnt = Number(_e.querySelector('[name="capacitorList[][pcs]"]').value);
                            }
                            if (_e.getAttribute('data-isatMax')) { // Converter Simulation Tool
                                paramList.isatMax = Number(_e.getAttribute('data-isatMax'));
                            }

                            infoPartList.push(paramList);
                        }
                    }
                }
            }

            if (infoPartList.length) {
                return infoPartList;
            }
        } else {
            SEM.console.log('getInfoPartList func: argument value error.');
        }
    },
    /** 다운로드 정보
     * @function SEM.chart.getInfoDown
     * @param {string} selectedPartId 파트 목록 대상 ID
     * @return {object} 다운로드에 필요한 정보
     */
    getInfoDown: function (selectedPartId, downModel, downType, downFileType) {
        var semChart = SEM.chart;
        var infoPart = semChart.getInfoPartList(selectedPartId);
        var infoDown = {};

        infoDown.downloadModel = downModel; // 다운로드
        infoDown.downloadType = downType; // 다운로드
        infoDown.downloadFileType = downFileType; // 다운로드
        infoDown.paramList = infoPart; // Selected Parts 정보

        return infoDown;
    },
    /**
     * 차트 그릴 때 필요한 정보 가져오기 - ajax request data
     * @function SEM.chart.getInfoData
     * @param {string} typeObj 차트 유형
     * @param {object} targetObj 정보 가져올 대상
     * @return {object} 선택한 정보
     */
    getInfoData: function (typeObj, targetObj) {
        targetObj = targetObj || {
            selectedPartId: 'selectedList', // default id 값 : Selected Parts (대상 목록의 복수 정보)
            modelModeName: 'modelTypeList', // default name 값 : Model Mode (체크박스 value 정보)
            mountingName: 'mountingTypeList', // default name 값 : Mouting (체크박스 value 정보)
            solderName: 'solderTypeList' // default name 값 : Solder (체크박스 value 정보)
        };
        var semChart = SEM.chart;
        var info = {}; // ajax request data
        var simulationType = {
            '|Z|': 'TEMPDC',
            'R': 'TEMPDC',
            '|X|': 'TEMPDC',
            '|Xs|': 'TEMPDC',
            '|Z|_R': 'TEMPDC',
            'C': 'TEMPDC',
            'L': 'TEMPDC',
            'Q': 'TEMPDC',
            'DF': 'TEMPDC',
            'SDB': 'TEMPDC',
            'Smithchart': 'TEMPDC',
            'LTemp': 'TEMPDC',
            'ACRf': 'TEMPDC',
            'Ls': 'TEMPDC',
            'Rs': 'TEMPDC',
            '|Z|_Rs': 'TEMPDC',
            'DCBias': 'CHAR',
            'ACVolt': 'CHAR',
            'RippleCurr': 'CHAR',
            'TCC': 'CHAR',
            'AppliedV': 'CHAR',
            'AppliedI': 'CHAR',
            'AppliedVI': 'CHAR',
            'DCBiasByTemp': 'TCCDC',
            'TCCbyDC': 'TCCDC',
            'LCurrent': 'Itemp_Isat',
            'TempRise': 'Itemp_Isat',
            'InductorVoltage': 'SimpleRipple',
            'InductorCurrent': 'SimpleRipple',
            'RippleVoltage': 'SimpleRipple',
            'Efficiency': 'EfficiencyLoss',
            'InductorLoss': 'EfficiencyLoss'
        };

        info.graphType = typeObj.chartType;
        if (simulationType.hasOwnProperty(typeObj.chartType)) {
            info.simulationType = simulationType[typeObj.chartType];
        }
        if (typeObj.circuitType) {
            info.sParamCircuit = typeObj.circuitType;
        }

        if (!targetObj) return info;

        if (targetObj.hasOwnProperty('selectedPartId')) {
            var infoPart = semChart.getInfoPartList(targetObj.selectedPartId); // Selected Parts 정보
            if (infoPart) {
                info.paramList = infoPart;
            }
        }
        if (targetObj.hasOwnProperty('modelModeName')) {
            var modelModeChecked = getCheckedValue(targetObj.modelModeName); // Selected Model Mode 정보
            if (modelModeChecked) {
                info.modelTypeList = modelModeChecked;
            }
        }
        if (targetObj.hasOwnProperty('mountingName')) {
            var mountingChecked = getCheckedValue(targetObj.mountingName); // Mounting Model Mode 정보
            if (mountingChecked) {
                info.mountingTypeList = mountingChecked;
            }
        }
        if (targetObj.hasOwnProperty('solderName')) {
            var solderChecked = getCheckedValue(targetObj.solderName); // Solder Model Mode 정보
            if (solderChecked) {
                info.solderTypeList = solderChecked;
            }
        }

        /* 체크된 항목 가져오기 */
        function getCheckedValue(name) {
            var _e, checkedValue = [];
            var list = document.querySelectorAll('input[name^="' + name + '"]');

            if (list.length) {
                for (var idx = 0; idx < list.length; idx++) {
                    _e = list[idx];
                    var chk = _e.checked;

                    if (chk) {
                        checkedValue.push(_e.value);
                    }
                }
                if (checkedValue.length) return checkedValue;
            }
        }

        /* Converter Simulation Tool */
        if (document.getElementById('converterType')) {
            var _dataType = document.getElementById('selectedPartsTool').getAttribute('data-type');
            var sType = _dataType === 'default-inductor' ? 'Inductor' : 'Capacitor';
            info.standardType = sType;

            info.converterType = document.getElementById('converterType').value;
            info.modulation = document.getElementById('modulation').value;
            info.temp = Number(document.getElementById('converterTemp').value);
            info.vin = Number(document.getElementById('converterVin').value);
            info.vout = Number(document.getElementById('converterVout').value);
            info.frequency = Number(document.getElementById('converterFreq').value);
            info.adc = Number(document.getElementById('converterAdc').value);
            info.swRise = Number(document.getElementById('swRise').value);
            info.swRon = Number(document.getElementById('swRon').value);

            var inductorPart = semChart.getInfoPartList('selectedInductor'); // Selected Parts 정보
            if (inductorPart) {
                info.inductorList = inductorPart;
            }
            var capacitorPart = semChart.getInfoPartList('selectedCapacitor'); // Selected Parts 정보
            if (capacitorPart) {
                info.capacitorList = capacitorPart;
            }
        }

        return info;
    },
    /**
     * 데이터 통신
     * @function SEM.chart.transferData
     * @param {object} typeObj 사용자가 클릭한 버튼의 차트 유형
     * @param {object} targetObj 가져올 정보 대상들
     */
    transferData: function (typeObj, targetObj) {
        var semChart = this;
        semChart.tempInfo = semChart.getInfoData(typeObj, targetObj); // request data

        SEM.console.log(semChart.tempInfo);

        $.ajax({
            url: $('#productGraphUrl').val(),
            type: "POST",
            dataType: "json",
            timeout: 30000,
            data: JSON.stringify(semChart.tempInfo),
            contentType: "application/json",
            beforeSend: function (xhr) {
            	 var token = $('input[name="_csrf"]').val();
 	            var header =  $('input[name="_csrf_header"]').val();
 	            
 	            xhr.setRequestHeader(header, token);
                var chkInfo = semChart.renderLayer(typeObj.chartType); // 레이어 생성
                if (chkInfo) { // 해당하는 옵션 유무 확인
                    semChart.setLazyLoad(); // 레이어 로딩
                    semChart.setEventLayer(); // 레이어 이벤트 등록
                } else {
                    return false;
                }

                if ($('#toggleGraph').length) {
                    semChart.toggleChart.show(); // 차트 show
                    $('#toggleGraph').prop('checked', true); // 차트 토글 버튼 on
                }
            },
            success: function (data, status, xhr) {
                if ($.isEmptyObject(data)) {
                    if (document.getElementById('converterType')) {
                        //Simulation Tool
                        alert('没有可以生成的图形。');
                    } else {
                        semChart.requestData(); // 데이터 요청 여부 확인
                    }
                    semChart.closeLayer(semChart.chartTempIdx);
                    semChart.isRun = false; // 차트 실행 가능으로 변경
                } else {
                    semChart.chartOriginData[semChart.chartTempIdx] = data; // 원본데이터 보관
                    semChart.afterGetData(typeObj.chartType);
                }
                semChart.resetPartlistAttr('selectedPartsTool');
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert("您要求处理中遇到了问题。");

                semChart.closeLayer(semChart.chartTempIdx);
                semChart.resetPartlistAttr('selectedPartsTool');
                semChart.isRun = false; // 차트 실행 가능으로 변경
            }
        });
    },
    /**
     * 차트 세팅 시작
     * @function SEM.chart.settingChart
     * @param {object} typeObj 사용자가 클릭한 버튼의 차트 유형
     * @param {object} targetObj 가져올 정보 대상들
     */
    settingChart: function (typeObj, targetObj) {
        var semChart = this; // SEM.chart

        semChart.transferData(typeObj, targetObj); // 데이터 주고 받기
    }
};

SEM.chart.eventListener();