/**
 * jqxgrid head column 셋팅
 * @return
 */
Common.prototype.getListHeadColumn = function(){
	SEM.console.time('getListHeadColumn');
	var _self = this;

	//custom render 구조 set
	var obj = {
		"alignCenter" : "center",
		"columnRenderer" : function(value){
			var textWithLineBreak = value.replace('\w', '<br />');
			return '<div style="display:table; width:100%; height:100%;"><span style="display:table-cell; text-align:center; vertical-align:middle;">' + textWithLineBreak + '</span></div>';
		},
		"searchRenderer" : function(value){
			var textWithLineBreak = value.replace('\w', '<br />');
			return '<div style="display:table; width:100%; height:100%; background:#ecf4ff;"><span style="display:table-cell; text-align:center; vertical-align:middle;">' + textWithLineBreak + '</span></div>';
		},
		"cellsRenderer" : function(row, columnfield, value, defaulthtml, columnproperties){
			var effectiveCap = _self.dataAdapter.records[row].effectiveCap;
			var effectiveUf = _self.dataAdapter.records[row].effectiveUf;
			var effectiveUnit = _self.dataAdapter.records[row].effectiveUnit;
			var capacitanceVal = _self.dataAdapter.records[row].capacitanceVal;
			var capaUnit = _self.dataAdapter.records[row].capacitanceUnit;
			var lWmm = _self.dataAdapter.records[row].lWmm;
			var dataLink = _self.dataAdapter.records[row].datasheet;
			var partNumber = _self.dataAdapter.records[row].partNumber;//20200707
			var html = "";
			var gTag = "gtag('event', 'list_ds_click', {'event_category':'MLCCEC', 'event_label':'SEM_CL_W_CN'});";
			if(columnfield === "partNumber"){
				html += '<div class="jqx-grid-cell-middle-align partNumber_cell"  style="margin-top:8.5px">';
				// html += '	<input type="checkbox" name="gridPartsChk" value="' + partNumber + '" class="grid_checkbox" title="Selected Parts" onClick="common.gridCellChk(this);" />' + partNumber;
				html += '	<button type="button" onclick="common.gridCellChk(this);" class="grid_cell_chk" data-row="' + row + '"> select </button>';
				// 특정고객일 경우 링크 X
				if($("#header").hasClass("customer")){
					html += partNumber;
				} else{
					html += '<a href="'+$("#prod_outsitelink").val()+'/cn/mlcc/'+partNumber+'.do" target="_blank" title="Go to new window">'+partNumber+'</a>';
				}
				html += '</div>'
				return html;
			};
			if(columnfield === "datasheet"){
				html += '<div class="jqx-grid-cell-middle-align datasheet_cell" style="margin-top:8px">';
				html += '	<a href="javascript:void(0);" onclick="dataSheetCheck('+ 'this,' + '\'' + partNumber + '\'' +' , ' + '\'datasheet\'' + '); '+ gTag +'" class="data"' + '>' + '<span class="ico_data">' + '</span>' + '</a>';
				html += '</div>'
				return html;
			};
			html += '<div class="jqx-grid-cell-middle-align" style="margin-top:8.5px">';
			switch(columnfield){
				case "effectiveUf" :
					(effectiveCap == null) ? (html+= "") : (html+= effectiveUf);
					break;
				case "capacitanceUf" :
					html+= capacitanceVal + capaUnit;
					break;
				case "lWinch" :
					if(value !== "") html+= value + '/' + lWmm;
					break;
				case "ratedVdc" :
					if(value !== "") html+= value + "Vdc";
					break;
				case "tSizeMax" :
					if(value !== "") html+= value + "mm";
					break;
				default :
					break;
			}
			html += '</div>';
             return html;
		},
		"cellClassName" : function(row, column, value, data){
			return _self.checkedRow[0].has(row) ? "chk_active" : "";
		}
	};

	//column 세부 정보 set
	var tempColumnInfo = [{
		text : "型号",
		datafield : "partNumber",
		width : "14%",
		cellsalign : obj.alignCenter,
		renderer : obj.columnRenderer,
		cellsrenderer : obj.cellsRenderer,
		cellclassname : obj.cellClassName,
		exportable : false
	},{
		text : "数据",
		datafield : "datasheet",
		width : "4%",
		cellsalign : obj.alignCenter,
		renderer : obj.columnRenderer,
		cellsrenderer : obj.cellsRenderer,
		cellclassname : obj.cellClassName,
		exportable : false
	},{
		text : "有效容值",
		datafield : "effectiveUf",
		width : "10%",
		hidden : true,
		cellsalign : obj.alignCenter,
		renderer : obj.searchRenderer,
		cellsrenderer : obj.cellsRenderer,
		cellclassname : obj.cellClassName,
	},{
		text : "|Z| (mohm)",
		datafield : "z",
		width : "10%",
		hidden : true,
		cellsalign : obj.alignCenter,
		renderer : obj.searchRenderer,
		cellclassname : obj.cellClassName,
	},{
		text : "等效串联电阻	(mohm)",
		datafield : "esr",
		width : "10%",
		hidden : true,
		cellsalign : obj.alignCenter,
		renderer : obj.searchRenderer,
		cellclassname : obj.cellClassName,
	},{
		text : "等效串联电感	(pH)",
		datafield : "esl",
		width : "10%",
		hidden : true,
		cellsalign : obj.alignCenter,
		renderer : obj.searchRenderer,
		cellclassname : obj.cellClassName,
	},{
		text : "用途",
		datafield : "useFor",
		width : "10%",
		cellsalign : obj.alignCenter,
		renderer : obj.columnRenderer,
		cellclassname : obj.cellClassName,
	},{
		text : "容量",
		datafield : "capacitanceUf",
		width : "10%",
		cellsalign : obj.alignCenter,
		renderer : obj.columnRenderer,
		cellsrenderer : obj.cellsRenderer,
		cellclassname : obj.cellClassName,
	},{
		text : "公差",
		datafield : "tolerance",
		width : "10%",
		cellsalign : obj.alignCenter,
		renderer : obj.columnRenderer,
		cellclassname : obj.cellClassName,
	},{
		text : "尺寸(Inch/mm)",
		datafield : "lWinch",
		width : "12%",
		cellsalign : obj.alignCenter,
		renderer : obj.columnRenderer,
		cellsrenderer : obj.cellsRenderer,
		cellclassname : obj.cellClassName,
	},{
		text : "额定电压",
		datafield : "ratedVdc",
		width : "10%",
		cellsalign : obj.alignCenter,
		renderer : obj.columnRenderer,
		cellsrenderer : obj.cellsRenderer,
		cellclassname : obj.cellClassName,
	},{
		text : "温度特性 ",
		datafield : "tcc",
		width : "7.5%",
		cellsalign : obj.alignCenter,
		renderer : obj.columnRenderer,
		cellclassname : obj.cellClassName,
	},{
		text : "厚度最大值",
		datafield : "tSizeMax",
		width : "10%",
		cellsalign : obj.alignCenter,
		renderer : obj.columnRenderer,
		cellsrenderer : obj.cellsRenderer,
		cellclassname : obj.cellClassName,
	},{
		text : "种类",
		datafield : "features",
		width : "12.5%",
		sizeMode: "wrap",
		cellsalign : obj.alignCenter,
		renderer : obj.columnRenderer,
		cellclassname : obj.cellClassName,
	}];
	SEM.console.timeEnd('getListHeadColumn');
	return tempColumnInfo;
};

/**
 * partsBoxAdd :: selected parts 영역으로 요소 추가
 */
Common.prototype.partsBoxAdd = function(e){
	SEM.console.time('partsBoxAdd');
	var _self = this;
	var row = e.args.rowindex;
	var dataRow =  $(_self.gridTarget).jqxGrid('getrowdata', row);
	var html = [];
	var gTag_ds = "gtag('event', 'select_click_ds', {'event_category':'MLCCEC', 'event_label':'SEM_CL_W_CN'});";
	var gTag_copy = "gtag('event', 'select_item_copy', {'event_category':'MLCCEC', 'event_label':'SEM_CL_W_CN'});";
	//$("#selectedList").find("li").removeClass("on").find(".parts_checkbox").prop("checked" , false);

	// temp,vdc 설정 값 없는 part의 경우 li에 fix_type class추가, input readonly 추가
	var role = `data-gridid="${_self.gridTarget.id}" data-rowidx="${row}"`;
	(dataRow.tcc === "C0G" || dataRow.tcc === "X8G" || dataRow.tempMeasurableYn === "N") ? html.push(`<li class="fix_type on" ${role}>`) : html.push(`<li class="on" ${role}>`);
	html.push('	<div class="box_inner">');
	html.push('		<div class="top">');
	html.push('			<label><input type="checkbox" name="partsChk" value="' + dataRow.partNumber + '" class="parts_checkbox" data-tccdc="' + dataRow.tccdc_count + '" data-derating="' + dataRow.derating_count + '" title="Selected Parts" checked />'+ dataRow.partNumber  +'</label>');
	html.push('			<a href="javascript:void(0)" class="list_del"><img src="/resources/cn/images/common/selected_close.png" alt="" /></a>');
	html.push('		</div>');
	html.push('		<div class="cont">');
	html.push('			<div class="left">');
	html.push('					<input type="hidden" name="paramList[][partsName]" value="'+ dataRow.partNumber  +'" />');
	if((dataRow.tcc === "C0G" || dataRow.tcc === "X8G" || dataRow.tempMeasurableYn === "N")){
		html.push('				<input type="text" name="paramList[][vdc]" data-min="0" data-max="'+  dataRow.vdcMax +'" readonly class="valueInput" value="0" /><span class="unit">Vdc</span>');
	}else{
		html.push('				<input type="text" name="paramList[][vdc]" data-min="0" data-max="'+  dataRow.vdcMax +'" class="valueInput " value="0" /><span class="unit">Vdc</span>');
		html.push('				<p class="txt">(0 ~ '+  dataRow.vdcMax +')</p>');
	}
	html.push('			</div>');
	html.push('			<div class="right">');
	if((dataRow.tcc === "C0G" || dataRow.tcc === "X8G" || dataRow.tempMeasurableYn === "N")){
		html.push('				<input type="text" name="paramList[][degC]" data-min="'+ dataRow.tempMin +'" data-max="'+ dataRow.tempMax +'" readonly class="valueInput" value="25" /><span class="unit">degC</span>');
	}else{
		html.push('				<input type="text" name="paramList[][degC]" data-min="'+ dataRow.tempMin +'" data-max="'+ dataRow.tempMax +'" class="valueInput" value="25" /><span class="unit">degC</span>');
		html.push('				<p class="txt">('+ dataRow.tempMin +'~' + dataRow.tempMax + ')</p>');
	}
	html.push('			</div>');
	html.push('		</div>');
	html.push('		<a href="javascript:void(0)" class="plus" onclick="' + gTag_copy + '"></a>');
	html.push('		<div class="infor_view">');
	html.push('			<table>');
	html.push('				<colgroup>');
	html.push('					<col width="97px;">');
	html.push('					<col width="133px">');
	html.push('				</colgroup>');
	html.push('				<thead>');
	html.push('				<tr>');
	html.push('					<th>特性</th>');
	html.push('					<th>数值</th>');
	html.push('				</tr>');
	html.push('				</thead>');
	html.push('				<tbody>');
	html.push('				<tr>');
	html.push('					<td>容量</td>');
	html.push('					<td>' + dataRow.capacitanceVal +''+ dataRow.capacitanceUnit +'</td>');
	html.push('				</tr>');
	html.push('				<tr>');
	html.push('					<td>额定电压</td>');
	html.push('					<td>' + dataRow.ratedVdc +'Vdc</td>');
	html.push('				</tr>');
	html.push('				<tr>');
	html.push('					<td>温度特性</td>');
	html.push('					<td>' + dataRow.tcc +'</td>');
	html.push('				</tr>');
	html.push('				<tr>');
	html.push('					<td>尺寸</td>');
	html.push('					<td>' + dataRow.lWinch +'(inch), ' + dataRow.lWmm + '(mm)</td>');
	html.push('				</tr>');
	html.push('				</tbody>');
	html.push('			</table>');
	html.push('			<div class="btn_area">');
	html.push('				<a href="javascript:void(0);" onclick="dataSheetCheck('+ 'this,' + '\'' + dataRow.partNumber + '\'' +' , ' + '\'datasheet\'' + '); '+ gTag_ds +'"><img src="/resources/cn/images/mlcc/btn_datasheet.jpg"pg" alt="" /></a>');
	html.push('			</div>');
	html.push('		</div>');
	html.push('	</div>');
	html.push('</li>');
	html = html.join('\n');
	$("#selectedList").prepend(html);
	$("#countText").text('(1)');
	gtag('event', 'select_item_'+ dataRow.partNumber +'', {'event_category':'MLCCEC', 'event_label':'SEM_CL_W_CN'});

	/* 요소 추가 시 팝업 활성화 */
	if(!$("#selectedPartsArea").hasClass("active")){
		$("#selectedPartsArea").addClass("active");
	}
	
	/* 문자 입력 방지 */
	$("#selectedList li.on").find('.valueInput').on('input', function () {
		this.value = this.value.replace(/[^0-9.-]/g, '').replace(/(\-.*)\-/g, '$1').replace(/(\..*)\./g, '$1');
	});

	common.deratingCheck();
	common.tccdcCheck();

	SEM.console.timeEnd('partsBoxAdd');
};

/**
 * derating check(derating 그래프 활성화 여부)
 */
Common.prototype.deratingCheck = function(){
	var deratingCnt = $("#selectedList").find("input:checked[data-derating='Y']").length;

	if(deratingCnt > 0){
		$("#graphTypeBtn").find(".derating_btn").prop("disabled" , false);
	}else{
		$("#graphTypeBtn").find(".derating_btn").prop("disabled" , true);
	};

	if($("#selectedList").find("input:checked").length == 0){
		$("#graphTypeBtn").find(".derating_btn").prop("disabled" , false);
	};
};

/**
 * tccdc check(tccdc 그래프 활성화 여부)
 */
Common.prototype.tccdcCheck = function(){
	var tccdcCnt = $("#selectedList").find("input:checked[data-tccdc='Y']").length;

	if(tccdcCnt > 0){
		$("#graphTypeBtn").find(".tccdc_btn").prop("disabled" , false);
	}else{
		$("#graphTypeBtn").find(".tccdc_btn").prop("disabled" , true);
	};

	if($("#selectedList").find("input:checked").length == 0){
		$("#graphTypeBtn").find(".tccdc_btn").prop("disabled" , false);
	};
};

/**
 * addFilterPanel(filter 요소 생성)
 */
Common.prototype.addFilterPanel = function(){
	SEM.console.time('addFilterPanel');
	var _self = this;
	var panelLeng = $("#filterArea").find(".panel").length;
	var recordsLength = _self.dataAdapter.records.length; //전체 리스트 갯수

	$("#filterArea").find(".panel").each(function(index,item){
		var $filterCont = $(item).find(".filter_cont"); //필터 패널 필터링 영역
		var innerType = $filterCont.attr("data-type"); //필터패널 타입
		var cellName = $filterCont.attr("data-cell"); //필터링을 연결할 grid header datafield
		var label;

		$(item).jqxPanel({ height: 155, sizeMode: "wrap"}); //패널 생성

		if(innerType === "input"){//input일 경우
			if(cellName === "partNumber"){
				$filterCont.find("input[type=text]").jqxInput({
					width:"80%",
					height: 30,
					placeHolder: $filterCont.find("input[type=text]").attr("placeholder"),
					minLength: 1
				});
			}
		}else if(innerType === "listbox"){ //listbox일 경우
			var sourceArr = []; // 전체선택 option 기본 셋팅
			
			//해당 datafield 리스트에서 data 중복 제거
			for(var i = 0; i < recordsLength; i++){
				//사이즈cell의 경우 2개의 data 조합해서 option 생성
				if(cellName === "lWinch"){
					var cellName2 = $filterCont.attr("data-cell2");
					label = _self.dataAdapter.records[i][cellName] + "/" + _self.dataAdapter.records[i][cellName2];
				}else{
					label = _self.dataAdapter.records[i][cellName];
				};
				if (sourceArr.indexOf(label) == -1) {
					sourceArr.push(label);
				};
			};
			/* 
			* 20190409 문자열 sort ascending 공통함수로 변경
			* sourceArr.sort().splice(0, 0, 'all'); 
			*/
			sourceArr = common.customSortFunc(sourceArr);
			sourceArr.splice(0, 0, 'all');

			/*
			* 20230203 tcc 필터 값 X7R(S) 순서 최하단 배치
			*/
			if(cellName === "tcc"){
				var targetText = "X7R(S)";
				var tIdx = sourceArr.indexOf(targetText);
				if(tIdx >= 0){
					sourceArr.splice(tIdx,1);
					sourceArr.push(targetText);
				};
			};

			$filterCont.jqxListBox({
				width: '100%',
				height:'100%',
				source: sourceArr,
				checkboxes: true
			});

			// $filterCont.jqxListBox('checkAll'); //listbox 전체 선택(기본값)
		}else if(innerType === "tab"){ //tab일 경우
			var $tabCont = $filterCont.find(".cont_inner"); // tab 내용영역

			$tabCont.each(function(n,elm){
				var $tabContType = $(elm).attr("data-stype"); //tab 스타일 (match or range)
				$(elm).find("input").each(function(i,o){
					$(o).jqxInput({
						width : 70,
						height : 20,
						minLength: 1,
						placeHolder : $(o).attr("placeholder")
					});
				});

				var $selectboxes = $(elm).find(".selectbox");
				//tab내용중 selectbox가 있을 경우 dropdownlist 생성(unit이 별개로 있을 경우)
				if($tabCont.find(".selectbox").length > 0 ){
					$selectboxes.each(function(selI, selB){
						var $selB = $(selB);
						var cellName = $selB.attr("data-cell");
						var sourceArr = [];

						//해당 datafield 리스트에서 data 중복 제거
						if(cellName === "capacitanceUnit" || cellName === "effectiveUnit"){
							// dropdownlist option 순서 때문에 강제 지정
							sourceArr = ["pF","nF", "uF"];
						}else{
							for(var i = 0; i < recordsLength; i++){
								var label = _self.dataAdapter.records[i][cellName];
								if (sourceArr.indexOf(label) == -1) {
									sourceArr.push(label);
								}
							}
						};

						var initIdx = _self.getDefaultUnitIndex($selB, sourceArr);
						// if(selectedIdx === -1) selectedIdx = 0;
						// console.log(selectedIdx)

						$selB.jqxDropDownList({
							width:50,
							height: "20px",
							enableBrowserBoundsDetection : true, //브라우저 창의 경계를 감지 해 드롭다운의 위치를 자동으로 조정
							autoDropDownHeight : true, //option높이의 합계로 높이 자동 지정
							source: sourceArr,
							selectedIndex: initIdx
						});

						var $pairedInput = $selB.siblings(".valueInput");
						$pairedInput.attr("data-valUnit" , sourceArr[initIdx]);
					});
				}
			});
		};
		if( index === (panelLeng-1) ){
			$("#filterArea").removeClass("load");
			$("#gridLoader").remove();
		};
	});
	SEM.console.timeEnd('addFilterPanel');

	/* filter tab event */
	$("#filterArea").find(".panel").each(function(index,item){
		$(item).find(".tab_btn").find("a").click(function(e){
			e.preventDefault();
			var idx = $(this).index();
			$(this).addClass("on").siblings().removeClass("on");
			$(item).find(".tab_cont").find(".cont_inner").eq(idx).addClass("on").siblings().removeClass("on");
		});
	});
	$(".filter_btn_area a").on("click", function(){
		$(this).addClass("on").siblings().removeClass("on");
	});

	_self.filterEventListener();
};

function formatNumber(val, decimalDigits, expDigits){
	decimalDigits = decimalDigits === undefined ? 6 :decimalDigits;
	expDigits = expDigits === undefined ? 1 : expDigits; // 유효숫자 2개까지

	var threshold = Math.pow(10, -decimalDigits); //decimalDigits=6은 0.000001

	var num = Number(val);
	if(isNaN(num)) return val;
	if(num === 0) return "0";

	var absNum = Math.abs(num);
	if(absNum < threshold){
		return num.toExponential(expDigits);
	};

	var fixed = num.toFixed(decimalDigits);
	return Number(fixed).toString();
}

/**
 * update Data 데이터 새로 받아오기 :: 작업중
     //http://jsfiddle.net/hristoxux/6wgbgc08/
*/
Common.prototype.advancedSearch = function(searchObj){
	SEM.console.time('advancedSearch');
	var _self = this;
	/* dummy data
	var data = [
		{
			"partNumber" : "CLR5A105MQ2CNN",
			"datasheet" : "data.do?partNum=CLR5A105MQ2CNN",
			"useFor" : "general",
			"capacitanceVal" : 15,
			"capacitanceUnit" : "uF",
			"capacitanceUf" : 15,
			"lWinch" : "0306",
			"lWmm" : "0816",
			"ratedVdc" : 4,
			"tcc" : "X7S",
			"tSizeMax" : 0.55,
			"tolerance" : "±20 %",
			"features" : "Low ESL(LICC)",
			"vdcMax" : 4,
			"tempMin" : -55,
			"tempMax" : 85,
			"z" : 5,
			"esr" : 5,
			"esl" : 5,
		},
		{
			"partNumber" : "CL03C0R3BA3GNN",
			"datasheet" : "data.do?partNum=CL03C0R3BA3GNN",
			"useFor" : "general",
			"capacitanceVal" : 10,
			"capacitanceUnit" : "nF",
			"capacitanceUf" : 0.01,
			"lWinch" : "0306",
			"lWmm" : "0816",
			"ratedVdc" : 25,
			"tcc" : "X6S",
			"tSizeMax" : 0.55,
			"tolerance" : "±20 %",
			"features" : "Low ESL(LICC)",
			"vdcMax" : 4,
			"tempMin" : -55,
			"tempMax" : 105,
			"z" : 10,
			"esr" : null,
			"esl" : 10,
		},
		{
			"partNumber" : "CL03C0R4NA3GNN",
			"datasheet" : "data.do?partNum=CL03C0R4NA3GNN",
			"useFor" : "general",
			"capacitanceVal" : 5,
			"capacitanceUnit" : "pF",
			"capacitanceUf" : 0.000005,
			"lWinch" : "0306",
			"lWmm" : "0816",
			"ratedVdc" : 22,
			"tcc" : "C0G",
			"tSizeMax" : 0.55,
			"tolerance" : "±20 %",
			"features" : "Low ESL(LICC)",
			"vdcMax" : 0,
			"tempMin" : -55,
			"tempMax" : 125,
			"z" : 15,
			"esr" : 15,
			"esl" : 15,
		}
	];
	*/
	var filterGridClass = "";
	var $advancedPop = $("#advancedPop");
	var submitObj = {
		dcBias : "",
		temp : "",
		selectArr : []
	};
	
	//valudation :: search 항목을 선택하지 않았을때.
	if($("#searchList").find("input[type=checkbox]:checked").length === 0){
		alert("请选择检索条件。");
		$("#searchList").find("input[type=checkbox]").eq(0).focus();
		return false;
	};

	submitObj["dcBias"] = $("#dcBias").val();
	submitObj["temp"] = $("#temp").val();
	$("#searchList").find("input[type=checkbox]:checked").each(function(index,item){
		var $parent = $(item).closest("li");
		var obj = {};

		//valudation :: checkbox선택 후 주파수 선택하지 않았을때
		if($parent.find("input[name=val]").val() === ""){
			alert("请设置频率的搜索条件。");
			$parent.find("input[name=val]").focus();
			return false;
		};

		obj["name"] = $(item).val();
		obj["value"] = $parent.find("input[name=val]").val();
		obj["unit"] = $parent.find("select[name=unit]").val();
		obj["gridField"] = $(item).val();
		switch($(item).val()){
			case "effectiveCap" :
				obj["title"] = "有效容值";
				obj["gridField"] = "effectiveUf";
				break;
			case "z" :
				obj["title"] = "|Z| (mohm)";
				break;
			case "esr" :
				obj["title"] = "ESR (mohm)";
				break;
			case "esl" :
				obj["title"] = "ESL (pH)";
				break;
		};
		submitObj["selectArr"].push(obj);
	});
	if($("#searchList").find("input[type=checkbox]:checked").length === submitObj["selectArr"].length){
		$advancedBtn.click();
		$.ajax({
			url : '/mlcc/advancedSearch.do',
			type : "POST",
			timeout: 30000,
			data : JSON.stringify(submitObj),
			contentType: "application/json",
			beforeSend: function (xhr) {
				_self.loader();
				 var token = $('input[name="_csrf"]').val();
		            var header =  $('input[name="_csrf_header"]').val();
		            
		            xhr.setRequestHeader(header, token);
			},
			
			success: function (data, status, xhr) {
				
				for(var i = 0; i < data.length; i++){
					data[i].tolerance =	data[i].tolerance.replace("@@", "±")
				}
				
				var searchObj = submitObj["selectArr"];
				var searchObjLen = submitObj["selectArr"].length;
				var searchEffectiveSearchUnit = searchObj[0].unit;
				SEM.console.log(data.resultList);

				//uf단위로 값 변환 후 데이터 추가
				$.each(data ,function(index,item){
					switch(item.capacitanceUnit){
						case "pF" :
							var filterLabel = item.capacitanceVal / (Math.pow(10, 6));
							break;
						case "nF" :
							var filterLabel = item.capacitanceVal / (Math.pow(10, 3));
							break;
						default :
							var filterLabel = item.capacitanceVal;
							break;
					};
					item["capacitanceUf"] = filterLabel;
					switch(searchEffectiveSearchUnit){
						case "pF" :
							var effLabel = item.effectiveCap * (Math.pow(10, 6));
							break;
						case "nF" :
							var effLabel = item.effectiveCap * (Math.pow(10, 3));
							break;
						default :
							var effLabel = item.effectiveCap;
							break;
					};
					item["effectiveUf"] = formatNumber(effLabel);
				});

				 _self.source.localdata = data;
				 _self.searchReset({columns :  true});

				for(var i = 0; i < searchObjLen; i++){
					var gridFieldName = searchObj[i]["gridField"];
					var subT = "";
					if(searchObj[i]["unit"] != undefined){
						if(searchObj[i]["value"] == undefined){
							subT = "(" + searchObj[i]["unit"] + ")";
						}else{
							subT = "<br />" + searchObj[i]["value"] + searchObj[i]["unit"];
						};
					};
					$(_self.gridTarget).jqxGrid('showcolumn', gridFieldName);
					$(_self.gridTarget) .jqxGrid ( 'setcolumnproperty', gridFieldName, 'text', searchObj[i]["title"] + subT );
					$("#filterArea").find("." + gridFieldName).removeClass("hidden");
					$("#filterArea").find("." + gridFieldName).find(".filter_unit").text(searchObj[i]["unit"]);
					$("#filterArea").find("." + gridFieldName).find(".search_info").remove();
					$("#filterArea").find("." + gridFieldName).find(".cont_inner").append(`<div class="search_info">DC Bias : ${submitObj.dcBias} Vdc <br>Temp. : ${submitObj.temp} degC</div>`);
				};
				$("#filterArea").attr("data-search" , "type" + searchObjLen);
				$(_self.gridTarget).jqxGrid('updatebounddata', 'cells');
				$("#gridLoader").remove(); //load close
				$(_self.gridTarget).trigger("filter");
			},
			complete: function(){

			},
			error: function (jqXHR, textStatus, errorThrown) {
				$("#gridLoader").remove(); //load close
				alert("您要求处理中遇到了问题。");
			   //SEM.console.log('errorThrown: ' + errorThrown);
			}
		});
	};
	 SEM.console.timeEnd('advancedSearch');
};
Common.prototype.pnCrossing = function(){
	SEM.console.time('pnCrossing');
	var value = $('#pnInput').val();
	var _self = this;
	var submitObj = {
		partNumber : value
	};
	if(value !== ""){
		if(value.length < 14){
			alert("请输入完整型号。");
			return;
		}else{
			$.ajax({
				url : '/mlcc/pncrossingSearch.do',
				type : "POST",
				timeout: 30000,
				data : JSON.stringify(submitObj),
				contentType: "application/json",
				beforeSend: function(xhr){
					_self.loader();
					 var token = $('input[name="_csrf"]').val();
		            var header =  $('input[name="_csrf_header"]').val();
		            
		            xhr.setRequestHeader(header, token);
				},
				success: function (data, status, xhr) {
					//적합한 파트 없을 시 
					if(data.length == 0){
						alert("我司数据库中没有找到您正在检索的器件。\n\n我们无法找到对应的机种，或因本工具的功能有限，建议您从＜产品检索＞通过筛选参数进行查询；\n或请联系SEMCO销售担当或技术工程师。");
						$("#gridLoader").remove(); //load close
						return false;
					}else{
						$pnBtn.click();
						$pnClossingPop.find("input[name=pnInput]").val();
						//uf단위로 값 변환 후 데이터 추가
						$.each(data ,function(index,item){
							switch(item.capacitanceUnit){
								case "pF" :
									var filterLabel = item.capacitanceVal / (Math.pow(10, 6));
									break;
								case "nF" :
									var filterLabel = item.capacitanceVal / (Math.pow(10, 3));
									break;
								default :
									var filterLabel = item.capacitanceVal;
									break;
							};
							item["capacitanceUf"] = filterLabel;
						});
						 _self.source.localdata = data;
						_self.searchReset();
						$("#filterArea").attr("data-search" , "type_PN");
						$(_self.gridTarget).jqxGrid('updatebounddata', 'cells');
						$("#gridLoader").remove(); //load close
						$(_self.gridTarget).trigger("filter");
					};
				},
				complete: function(){
	
				},
				error: function (jqXHR, textStatus, errorThrown) {
					$("#gridLoader").remove(); //load close
					alert("您要求处理中遇到了问题。");
				   //SEM.console.log('errorThrown: ' + errorThrown);
				}
			});
		}
	}else{
		alert("请选择检索条件。");
	};
	SEM.console.timeEnd('pnCrossing');
};
Common.prototype.searchReset = function(options){
	var _self = this;
	SEM.console.time('searchReset');
	var searchList = ["effectiveUf","z","esr","esl"];

	options = options || {columns : true, inputs : true};
	if(options.columns){
		$("#filterArea").attr("data-search" , "");
		$("#filterArea").find(".search_panel ").addClass("hidden");
		for(var i = 0; i < searchList.length; i++){
			var field = searchList[i];
			var $searchPanael = $("#filterArea").find("." + field);
			$(_self.gridTarget).jqxGrid('hidecolumn', searchList[i]);
			$searchPanael.find("input.valueInput").each(function(){
				$(this).jqxInput("val" , "");
			});
			$(_self.gridTarget).jqxGrid("removefilter",field);
		};
	};
	if(options.inputs){
		$("#advancedPop").find("input").each(function(index,item){
			if($(item).attr("type") === "checkbox"){
				$(item).prop("checked" , false);
			}else if($(item).attr("type") === "text"){
				if($(item).attr("data-defaultval") == undefined){
					$(item).val("");
				}else{
					$(item).val($(item).attr("data-defaultval"));
				}
			};
		});
		$("#advancedPop").find("select[name=unit]").each(function(index,item){
			var $defaultPotion = $(item).find("option[selected]");
			if($defaultPotion.length > 0){
				$(item).val($defaultPotion.val());
			}else{
				$(item).prop("selectedIndex" , 0);
			}
		});
	}
	SEM.console.timeEnd('searchReset');
};
Common.prototype.loader = function(){
	SEM.console.time('loader');
	var loaderNode = '<div id="gridLoader" class="grid_loader"></div>';
	$("#contentWrap").find(".view_area").append(loaderNode);
	var $loader = $("#gridLoader");
		
	$loader.jqxLoader({
		text: "",
		width: 'auto',
		height: 'auto'
	});
	$loader.jqxLoader("open");
	SEM.console.timeEnd('loader');
};
var common = new Common(gridTarget,"mlccEcPartList");
common.addFilterPanel();

$("#advancedPop").on("keyup", "input[type=text]",function(){
	SEM.selectedParts.valueRangeSet($(this));
});
$("#asReset").on("click",function(){
	common.searchReset({inputs : true});
});