SEM.chart.chartTypeInfo = {
    '|Z|': {
        layerTitle: {
            backgroundColor: '#08b8f7',
            title: function () {
                var result = '阻抗';

                return result;
            }
        },
        axesType: {
            x: 'logarithmic',
            y: 'logarithmic'
        },
        label: {
            x: 'Frequency(MHz)',
            y: '|Z|(ohm)'
        },
        tooltipLabel: function (tooltipItem, data) {
            var idx = tooltipItem.datasetIndex; // 해당 차트 라인
            var lineInfo = data.datasets[idx]; // 해당 차트 라인 정보
            var layerIdx = this._chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var _digitX = parseFloat(Number(tooltipItem.xLabel).toFixed(5));
            var _digitY = 0;
            var _value;
            var vdc = lineInfo.vdc + 'Vdc';
            var degC = lineInfo.degC + 'degC';
            var valueX = 'Frequency: ' + tooltipItem.xLabel.convertUnit('M', 'Hz', [5]);
            var valueY = 'Impedance: ' + tooltipItem.yLabel.convertUnit('', 'ohm', [3, 5]);

            return [
                thisLayerData.graphType + ', ' + vdc + ', ' + degC + ', ' + lineInfo.modelType,
                valueX,
                valueY
            ];
        },
        legendCallback: function (chart) { // 범례 커스텀
            var legendHtml = [];
            var currentData, partName, vdc, degC, modelType, model;
            var dataset = chart.data.datasets;
            var layerIdx = chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var graphType = thisLayerData.graphType;

            legendHtml.push('<ul>');
            legendHtml.push('    <input type="hidden" id="saveDataGraphType' + layerIdx + '" name="graphType' + layerIdx + '" value="' + graphType + '"/>');
            legendHtml.push('	 <input type="hidden" id="saveSimulationType' + layerIdx + '" name="simulationType' + layerIdx + '" value="TEMPDC"/>');
            for (var i = 0; i < dataset.length; i++) {
                currentData = dataset[i];
                partName = currentData.label;
                vdc = currentData.vdc + 'Vdc';
                degC = currentData.degC + 'degC';
                modelType = currentData.modelType;

                if (modelType === 'Precise') {
                    model = modelType;
                    modelTypeOne = 'P';
                } else if (modelType === 'Simple') {
                    model = '(C(F) ' + currentData.simC.toExponential(2) + ' / L(H) ' + currentData.simL.toExponential(2) + ' / R(Ω) ' + currentData.simR.toExponential(2) + ')';
                    modelTypeOne = 'S';
                } else {
                    model = '';
                }

                legendHtml.push('    <li class="chart_legend on" style="color:' + currentData.borderColor + '" data-parts="' + partName + '">');
                legendHtml.push('		 <input type="hidden" name="partNumber" value="' + partName + '"/>');
                legendHtml.push('		 <input type="hidden" name="vdc" value="' + currentData.vdc + '"/>');
                legendHtml.push('		 <input type="hidden" name="degC" value="' + currentData.degC + '"/>');
                legendHtml.push('		 <input type="hidden" name="modelTypeOne" value="' + modelTypeOne + '"/>');
                legendHtml.push('        <a href="javascript:void(0);" class="chip" onclick="SEM.chart.setEventLegend(this, event, ' + '\'' + i + '\'' + ')"></a>');
                legendHtml.push('        <span class="parts_name">' + partName + ', ' + graphType + ', ' + vdc + ', ' + degC + ', ' + model + '</span>');
                legendHtml.push('        <button type="button" class="btn_remove" onclick="SEM.chart.removeLegend(this, event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ');">remove</button>');
                legendHtml.push('    </li>');
            }
            legendHtml.push('</ul>');

            return legendHtml.join('\n');
        }
    },
    'R': {
        layerTitle: {
            backgroundColor: '#08b8f7',
            title: function () {
                var result = '等效串联电阻';

                return result;
            }
        },
        axesType: {
            x: 'logarithmic',
            y: 'logarithmic',
        },
        label: {
            x: 'Frequency(MHz)',
            y: 'ESR(ohm)'
        },
        tooltipLabel: function (tooltipItem, data) {
            var idx = tooltipItem.datasetIndex; // 해당 차트 라인
            var lineInfo = data.datasets[idx]; // 해당 차트 라인 정보
            var layerIdx = this._chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var _digitX = parseFloat(Number(tooltipItem.xLabel).toFixed(5));
            var _digitY = 0;
            var _value;
            var vdc = lineInfo.vdc + 'Vdc';
            var degC = lineInfo.degC + 'degC';
            var valueX = 'Frequency: ' + tooltipItem.xLabel.convertUnit('M', 'Hz', [5]);
            var valueY = 'Resistance: ' + tooltipItem.yLabel.convertUnit('', 'ohm', [3, 5]);

            return [
                thisLayerData.graphType + ', ' + vdc + ', ' + degC + ', ' + lineInfo.modelType,
                valueX,
                valueY
            ];
        },
        legendCallback: function (chart) { // 범례 커스텀
            var legendHtml = [];
            var currentData, partName, vdc, degC, modelType, model;
            var dataset = chart.data.datasets;
            var layerIdx = chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var graphType = thisLayerData.graphType;

            legendHtml.push('<ul>');
            legendHtml.push('    <input type="hidden" id="saveDataGraphType' + layerIdx + '" name="graphType' + layerIdx + '" value="' + graphType + '"/>');
            legendHtml.push('	 <input type="hidden" id="saveSimulationType' + layerIdx + '" name="simulationType' + layerIdx + '" value="TEMPDC"/>');
            for (var i = 0; i < dataset.length; i++) {
                currentData = dataset[i];
                partName = currentData.label;
                vdc = currentData.vdc + 'Vdc';
                degC = currentData.degC + 'degC';
                modelType = currentData.modelType;

                if (modelType === 'Precise') {
                    model = modelType;
                    modelTypeOne = 'P';
                } else if (modelType === 'Simple') {
                    model = '(C(F) ' + currentData.simC.toExponential(2) + ' / L(H) ' + currentData.simL.toExponential(2) + ' / R(Ω) ' + currentData.simR.toExponential(2) + ')';
                    modelTypeOne = 'S';
                } else {
                    model = '';
                }

                legendHtml.push('    <li class="chart_legend on" style="color:' + currentData.borderColor + '" data-parts="' + partName + '">');
                legendHtml.push('		 <input type="hidden" name="partNumber" value="' + partName + '"/>');
                legendHtml.push('		 <input type="hidden" name="vdc" value="' + currentData.vdc + '"/>');
                legendHtml.push('		 <input type="hidden" name="degC" value="' + currentData.degC + '"/>');
                legendHtml.push('		 <input type="hidden" name="modelTypeOne" value="' + modelTypeOne + '"/>');
                legendHtml.push('        <a href="javascript:void(0);" class="chip" onclick="SEM.chart.setEventLegend(this, event, ' + '\'' + i + '\'' + ')"></a>');
                legendHtml.push('        <span class="parts_name">' + partName + ', ' + graphType + ', ' + vdc + ', ' + degC + ', ' + model + '</span>');
                legendHtml.push('        <button type="button" class="btn_remove" onclick="SEM.chart.removeLegend(this, event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ');">remove</button>');
                legendHtml.push('    </li>');
            }
            legendHtml.push('</ul>');

            return legendHtml.join('\n');
        }
    },
    '|X|': {
        layerTitle: {
            backgroundColor: '#08b8f7',
            title: function () {
                var result = '电抗';

                return result;
            }
        },
        axesType: {
            x: 'logarithmic',
            y: 'logarithmic'
        },
        label: {
            x: 'Frequency(MHz)',
            y: '|X|(ohm)'
        },
        tooltipLabel: function (tooltipItem, data) {
            var idx = tooltipItem.datasetIndex; // 해당 차트 라인
            var lineInfo = data.datasets[idx]; // 해당 차트 라인 정보
            var layerIdx = this._chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var _digitX = parseFloat(Number(tooltipItem.xLabel).toFixed(5));
            var _digitY = 0;
            var _value;
            var vdc = lineInfo.vdc + 'Vdc';
            var degC = lineInfo.degC + 'degC';
            var valueX = 'Frequency: ' + tooltipItem.xLabel.convertUnit('M', 'Hz', [5]);
            var valueY = 'Reactance: ' + tooltipItem.yLabel.convertUnit('', 'ohm', [3, 5]);

            return [
                thisLayerData.graphType + ', ' + vdc + ', ' + degC + ', ' + lineInfo.modelType,
                valueX,
                valueY
            ];
        },
        legendCallback: function (chart) { // 범례 커스텀
            var legendHtml = [];
            var currentData, partName, vdc, degC, modelType, model;
            var dataset = chart.data.datasets;
            var layerIdx = chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var graphType = thisLayerData.graphType;

            legendHtml.push('<ul>');
            legendHtml.push('    <input type="hidden" id="saveDataGraphType' + layerIdx + '" name="graphType' + layerIdx + '" value="' + graphType + '"/>');
            legendHtml.push('	 <input type="hidden" id="saveSimulationType' + layerIdx + '" name="simulationType' + layerIdx + '" value="TEMPDC"/>');
            for (var i = 0; i < dataset.length; i++) {
                currentData = dataset[i];
                partName = currentData.label;
                vdc = currentData.vdc + 'Vdc';
                degC = currentData.degC + 'degC';
                modelType = currentData.modelType;

                if (modelType === 'Precise') {
                    model = modelType;
                    modelTypeOne = 'P';
                } else if (modelType === 'Simple') {
                    model = '(C(F) ' + currentData.simC.toExponential(2) + ' / L(H) ' + currentData.simL.toExponential(2) + ' / R(Ω) ' + currentData.simR.toExponential(2) + ')';
                    modelTypeOne = 'S';
                } else {
                    model = '';
                }

                legendHtml.push('    <li class="chart_legend on" style="color:' + currentData.borderColor + '" data-parts="' + partName + '">');
                legendHtml.push('		 <input type="hidden" name="partNumber" value="' + partName + '"/>');
                legendHtml.push('		 <input type="hidden" name="vdc" value="' + currentData.vdc + '"/>');
                legendHtml.push('		 <input type="hidden" name="degC" value="' + currentData.degC + '"/>');
                legendHtml.push('		 <input type="hidden" name="modelTypeOne" value="' + modelTypeOne + '"/>');
                legendHtml.push('        <a href="javascript:void(0);" class="chip" onclick="SEM.chart.setEventLegend(this, event, ' + '\'' + i + '\'' + ')"></a>');
                legendHtml.push('        <span class="parts_name">' + partName + ', ' + graphType + ', ' + vdc + ', ' + degC + ', ' + model + '</span>');
                legendHtml.push('        <button type="button" class="btn_remove" onclick="SEM.chart.removeLegend(this, event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ');">remove</button>');
                legendHtml.push('    </li>');
            }
            legendHtml.push('</ul>');

            return legendHtml.join('\n');
        }
    },
    '|Z|_R': {
        layerTitle: {
            backgroundColor: '#08b8f7',
            title: function () {
                var result = '阻抗与电阻';

                return result;
            }
        },
        axesType: {
            x: 'logarithmic',
            y: 'logarithmic'
        },
        label: {
            x: 'Frequency(MHz)',
            y: '|Z|, ESR(ohm)'
        },
        tooltipLabel: function (tooltipItem, data) {
            var idx = tooltipItem.datasetIndex; // 해당 차트 라인
            var lineInfo = data.datasets[idx]; // 해당 차트 라인 정보
            var layerIdx = this._chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var _digitX = parseFloat(Number(tooltipItem.xLabel).toFixed(5));
            var _digitY = 0;
            var _value;
            var vdc = lineInfo.vdc + 'Vdc';
            var degC = lineInfo.degC + 'degC';
            var titleY = 'Resistance';

            if (lineInfo.graphSubType === '|Z|') {
                titleY = 'Impedance';
            }

            var valueX = 'Frequency: ' + tooltipItem.xLabel.convertUnit('M', 'Hz', [5]);
            var valueY = titleY + ': ' + tooltipItem.yLabel.convertUnit('', 'ohm', [3, 5]);

            return [
                lineInfo.graphSubType + ', ' + vdc + ', ' + degC + ', ' + lineInfo.modelType,
                valueX,
                valueY
            ];
        },
        legendCallback: function (chart) { // 범례 커스텀
            var legendHtml = [];
            var currentData, partName, subType, vdc, degC, modelType, model;
            var dataset = chart.data.datasets;
            var layerIdx = chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var graphType = thisLayerData.graphType;

            legendHtml.push('<ul>');
            legendHtml.push('    <input type="hidden" id="saveDataGraphType' + layerIdx + '" name="graphType' + layerIdx + '" value="' + graphType + '"/>');
            legendHtml.push('	 <input type="hidden" id="saveSimulationType' + layerIdx + '" name="simulationType' + layerIdx + '" value="TEMPDC"/>');
            for (var i = 0; i < dataset.length; i++) {
                currentData = dataset[i];
                partName = currentData.label;
                subType = currentData.graphSubType;
                vdc = currentData.vdc + 'Vdc';
                degC = currentData.degC + 'degC';
                modelType = currentData.modelType;

                if (modelType === 'Precise') {
                    model = modelType;
                    modelTypeOne = 'P';
                } else if (modelType === 'Simple') {
                    model = '(C(F) ' + currentData.simC.toExponential(2) + ' / L(H) ' + currentData.simL.toExponential(2) + ' / R(Ω) ' + currentData.simR.toExponential(2) + ')';
                    modelTypeOne = 'S';
                } else {
                    model = '';
                }

                legendHtml.push('    <li class="chart_legend on" style="color:' + currentData.borderColor + '" data-parts="' + partName + '">');
                legendHtml.push('		 <input type="hidden" name="partNumber" value="' + partName + '"/>');
                legendHtml.push('		 <input type="hidden" name="vdc" value="' + currentData.vdc + '"/>');
                legendHtml.push('		 <input type="hidden" name="degC" value="' + currentData.degC + '"/>');
                legendHtml.push('		 <input type="hidden" name="modelTypeOne" value="' + modelTypeOne + '"/>');
                legendHtml.push('        <a href="javascript:void(0);" class="chip" onclick="SEM.chart.setEventLegend(this, event, ' + '\'' + i + '\'' + ')"></a>');
                legendHtml.push('        <span class="parts_name">' + partName + ', ' + subType + ', ' + vdc + ', ' + degC + ', ' + model + '</span>');
                legendHtml.push('        <button type="button" class="btn_remove" onclick="SEM.chart.removeLegend(this, event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ');">remove</button>');
                legendHtml.push('    </li>');
            }
            legendHtml.push('</ul>');

            return legendHtml.join('\n');
        }
    },
    'C': {
        layerTitle: {
            backgroundColor: '#08b8f7',
            title: function () {
                var result = '有效容值';

                return result;
            }
        },
        axesType: {
            x: 'logarithmic',
            y: 'logarithmic'
        },
        label: {
            x: 'Frequency(MHz)',
            y: 'Effective Capacitance(uF)'
        },
        tooltipLabel: function (tooltipItem, data) {
            var idx = tooltipItem.datasetIndex; // 해당 차트 라인
            var lineInfo = data.datasets[idx]; // 해당 차트 라인 정보
            var layerIdx = this._chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var _digitX = parseFloat(Number(tooltipItem.xLabel).toFixed(5));
            var _digitY = 0;
            var _value;
            var vdc = lineInfo.vdc + 'Vdc';
            var degC = lineInfo.degC + 'degC';
            var valueX = 'Frequency: ' + tooltipItem.xLabel.convertUnit('M', 'Hz', [5]);
            var valueY = 'Capacitance: ' + tooltipItem.yLabel.convertUnit('u', 'F', [5]);

            return [
                thisLayerData.graphType + ', ' + vdc + ', ' + degC + ', ' + lineInfo.modelType,
                valueX,
                valueY
            ];
        },
        legendCallback: function (chart) { // 범례 커스텀
            var legendHtml = [];
            var currentData, partName, vdc, degC, modelType, model;
            var dataset = chart.data.datasets;
            var layerIdx = chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var graphType = thisLayerData.graphType;

            legendHtml.push('<ul>');
            legendHtml.push('    <input type="hidden" id="saveDataGraphType' + layerIdx + '" name="graphType' + layerIdx + '" value="' + graphType + '"/>');
            legendHtml.push('	 <input type="hidden" id="saveSimulationType' + layerIdx + '" name="simulationType' + layerIdx + '" value="TEMPDC"/>');
            for (var i = 0; i < dataset.length; i++) {
                currentData = dataset[i];
                partName = currentData.label;
                vdc = currentData.vdc + 'Vdc';
                degC = currentData.degC + 'degC';
                modelType = currentData.modelType;

                if (modelType === 'Precise') {
                    model = modelType;
                    modelTypeOne = 'P';
                } else if (modelType === 'Simple') {
                    model = '(C(F) ' + currentData.simC.toExponential(2) + ' / L(H) ' + currentData.simL.toExponential(2) + ' / R(Ω) ' + currentData.simR.toExponential(2) + ')';
                    modelTypeOne = 'S';
                } else {
                    model = '';
                }

                legendHtml.push('    <li class="chart_legend on" style="color:' + currentData.borderColor + '" data-parts="' + partName + '">');
                legendHtml.push('		 <input type="hidden" name="partNumber" value="' + partName + '"/>');
                legendHtml.push('		 <input type="hidden" name="vdc" value="' + currentData.vdc + '"/>');
                legendHtml.push('		 <input type="hidden" name="degC" value="' + currentData.degC + '"/>');
                legendHtml.push('		 <input type="hidden" name="modelTypeOne" value="' + modelTypeOne + '"/>');
                legendHtml.push('        <a href="javascript:void(0);" class="chip" onclick="SEM.chart.setEventLegend(this, event, ' + '\'' + i + '\'' + ')"></a>');
                legendHtml.push('        <span class="parts_name">' + partName + ', ' + graphType + ', ' + vdc + ', ' + degC + ', ' + model + '</span>');
                legendHtml.push('        <button type="button" class="btn_remove" onclick="SEM.chart.removeLegend(this, event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ');">remove</button>');
                legendHtml.push('    </li>');
            }
            legendHtml.push('</ul>');

            return legendHtml.join('\n');
        }
    },
    'L': {
        layerTitle: {
            backgroundColor: '#08b8f7',
            title: function () {
                var result = '有效感值';

                return result;
            }
        },
        axesType: {
            x: 'logarithmic',
            y: 'logarithmic'
        },
        label: {
            x: 'Frequency(MHz)',
            y: 'Effective Inductance(nH)'
        },
        tooltipLabel: function (tooltipItem, data) {
            var idx = tooltipItem.datasetIndex; // 해당 차트 라인
            var lineInfo = data.datasets[idx]; // 해당 차트 라인 정보
            var layerIdx = this._chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var _digitX = parseFloat(Number(tooltipItem.xLabel).toFixed(5));
            var _digitY = 0;
            var _value;
            var vdc = lineInfo.vdc + 'Vdc';
            var degC = lineInfo.degC + 'degC';
            var valueX = 'Frequency: ' + tooltipItem.xLabel.convertUnit('M', 'Hz', [5]);
            var valueY = 'Inductance: ' + tooltipItem.yLabel.convertUnit('n', 'H', [5]);

            return [
                thisLayerData.graphType + ', ' + vdc + ', ' + degC + ', ' + lineInfo.modelType,
                valueX,
                valueY
            ];
        },
        legendCallback: function (chart) { // 범례 커스텀
            var legendHtml = [];
            var currentData, partName, vdc, degC, modelType, model;
            var dataset = chart.data.datasets;
            var layerIdx = chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var graphType = thisLayerData.graphType;

            legendHtml.push('<ul>');
            legendHtml.push('    <input type="hidden" id="saveDataGraphType' + layerIdx + '" name="graphType' + layerIdx + '" value="' + graphType + '"/>');
            legendHtml.push('	 <input type="hidden" id="saveSimulationType' + layerIdx + '" name="simulationType' + layerIdx + '" value="TEMPDC"/>');
            for (var i = 0; i < dataset.length; i++) {
                currentData = dataset[i];
                partName = currentData.label;
                vdc = currentData.vdc + 'Vdc';
                degC = currentData.degC + 'degC';
                modelType = currentData.modelType;

                if (modelType === 'Precise') {
                    model = modelType;
                    modelTypeOne = 'P';
                } else if (modelType === 'Simple') {
                    model = '(C(F) ' + currentData.simC.toExponential(2) + ' / L(H) ' + currentData.simL.toExponential(2) + ' / R(Ω) ' + currentData.simR.toExponential(2) + ')';
                    modelTypeOne = 'S';
                } else {
                    model = '';
                }

                legendHtml.push('    <li class="chart_legend on" style="color:' + currentData.borderColor + '" data-parts="' + partName + '">');
                legendHtml.push('		 <input type="hidden" name="partNumber" value="' + partName + '"/>');
                legendHtml.push('		 <input type="hidden" name="vdc" value="' + currentData.vdc + '"/>');
                legendHtml.push('		 <input type="hidden" name="degC" value="' + currentData.degC + '"/>');
                legendHtml.push('		 <input type="hidden" name="modelTypeOne" value="' + modelTypeOne + '"/>');
                legendHtml.push('        <a href="javascript:void(0);" class="chip" onclick="SEM.chart.setEventLegend(this, event, ' + '\'' + i + '\'' + ')"></a>');
                legendHtml.push('        <span class="parts_name">' + partName + ', ' + graphType + ', ' + vdc + ', ' + degC + ', ' + model + '</span>');
                legendHtml.push('        <button type="button" class="btn_remove" onclick="SEM.chart.removeLegend(this, event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ');">remove</button>');
                legendHtml.push('    </li>');
            }
            legendHtml.push('</ul>');

            return legendHtml.join('\n');
        }
    },
    'Q': {
        layerTitle: {
            backgroundColor: '#08b8f7',
            title: function () {
                var result = '品质因数';

                return result;
            }
        },
        axesType: {
            x: 'logarithmic',
            y: 'logarithmic'
        },
        label: {
            x: 'Frequency(MHz)',
            y: 'Q'
        },
        tooltipLabel: function (tooltipItem, data) {
            var idx = tooltipItem.datasetIndex; // 해당 차트 라인
            var lineInfo = data.datasets[idx]; // 해당 차트 라인 정보
            var layerIdx = this._chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var _digitX = parseFloat(Number(tooltipItem.xLabel).toFixed(5));
            var _digitY = parseFloat(Number(tooltipItem.yLabel).toFixed(5));
            var _value;
            var vdc = lineInfo.vdc + 'Vdc';
            var degC = lineInfo.degC + 'degC';
            var valueX = 'Frequency: ' + tooltipItem.xLabel.convertUnit('M', 'Hz', [5]);
            var valueY = 'Q: ' + _digitY;

            return [
                thisLayerData.graphType + ', ' + vdc + ', ' + degC + ', ' + lineInfo.modelType,
                valueX,
                valueY
            ];
        },
        legendCallback: function (chart) { // 범례 커스텀
            var legendHtml = [];
            var currentData, partName, vdc, degC, modelType, model;
            var dataset = chart.data.datasets;
            var layerIdx = chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var graphType = thisLayerData.graphType;

            legendHtml.push('<ul>');
            legendHtml.push('    <input type="hidden" id="saveDataGraphType' + layerIdx + '" name="graphType' + layerIdx + '" value="' + graphType + '"/>');
            legendHtml.push('	 <input type="hidden" id="saveSimulationType' + layerIdx + '" name="simulationType' + layerIdx + '" value="TEMPDC"/>');
            for (var i = 0; i < dataset.length; i++) {
                currentData = dataset[i];
                partName = currentData.label;
                vdc = currentData.vdc + 'Vdc';
                degC = currentData.degC + 'degC';
                modelType = currentData.modelType;

                if (modelType === 'Precise') {
                    model = modelType;
                    modelTypeOne = 'P';
                } else if (modelType === 'Simple') {
                    model = '(C(F) ' + currentData.simC.toExponential(2) + ' / L(H) ' + currentData.simL.toExponential(2) + ' / R(Ω) ' + currentData.simR.toExponential(2) + ')';
                    modelTypeOne = 'S';
                } else {
                    model = '';
                }

                legendHtml.push('    <li class="chart_legend on" style="color:' + currentData.borderColor + '" data-parts="' + partName + '">');
                legendHtml.push('		 <input type="hidden" name="partNumber" value="' + partName + '"/>');
                legendHtml.push('		 <input type="hidden" name="vdc" value="' + currentData.vdc + '"/>');
                legendHtml.push('		 <input type="hidden" name="degC" value="' + currentData.degC + '"/>');
                legendHtml.push('		 <input type="hidden" name="modelTypeOne" value="' + modelTypeOne + '"/>');
                legendHtml.push('        <a href="javascript:void(0);" class="chip" onclick="SEM.chart.setEventLegend(this, event, ' + '\'' + i + '\'' + ')"></a>');
                legendHtml.push('        <span class="parts_name">' + partName + ', ' + graphType + ', ' + vdc + ', ' + degC + ', ' + model + '</span>');
                legendHtml.push('        <button type="button" class="btn_remove" onclick="SEM.chart.removeLegend(this, event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ');">remove</button>');
                legendHtml.push('    </li>');
            }
            legendHtml.push('</ul>');

            return legendHtml.join('\n');
        }
    },
    'DF': {
        layerTitle: {
            backgroundColor: '#08b8f7',
            title: function () {
                var result = '损耗';

                return result;
            }
        },
        axesType: {
            x: 'logarithmic',
            y: 'logarithmic'
        },
        label: {
            x: 'Frequency(MHz)',
            y: 'DF'
        },
        tooltipLabel: function (tooltipItem, data) {
            var idx = tooltipItem.datasetIndex; // 해당 차트 라인
            var lineInfo = data.datasets[idx]; // 해당 차트 라인 정보
            var layerIdx = this._chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var _digitX = parseFloat(Number(tooltipItem.xLabel).toFixed(5));
            var _digitY = parseFloat(Number(tooltipItem.yLabel).toFixed(5));
            var _value;
            var vdc = lineInfo.vdc + 'Vdc';
            var degC = lineInfo.degC + 'degC';
            var valueX = 'Frequency: ' + tooltipItem.xLabel.convertUnit('M', 'Hz', [5]);
            var valueY = 'DF: ' + _digitY;

            return [
                thisLayerData.graphType + ', ' + vdc + ', ' + degC + ', ' + lineInfo.modelType,
                valueX,
                valueY
            ];
        },
        legendCallback: function (chart) { // 범례 커스텀
            var legendHtml = [];
            var currentData, partName, vdc, degC, modelType, model;
            var dataset = chart.data.datasets;
            var layerIdx = chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var graphType = thisLayerData.graphType;

            legendHtml.push('<ul>');
            legendHtml.push('    <input type="hidden" id="saveDataGraphType' + layerIdx + '" name="graphType' + layerIdx + '" value="' + graphType + '"/>');
            legendHtml.push('	 <input type="hidden" id="saveSimulationType' + layerIdx + '" name="simulationType' + layerIdx + '" value="TEMPDC"/>');
            for (var i = 0; i < dataset.length; i++) {
                currentData = dataset[i];
                partName = currentData.label;
                vdc = currentData.vdc + 'Vdc';
                degC = currentData.degC + 'degC';
                modelType = currentData.modelType;

                if (modelType === 'Precise') {
                    model = modelType;
                    modelTypeOne = 'P';
                } else if (modelType === 'Simple') {
                    model = '(C(F) ' + currentData.simC.toExponential(2) + ' / L(H) ' + currentData.simL.toExponential(2) + ' / R(Ω) ' + currentData.simR.toExponential(2) + ')';
                    modelTypeOne = 'S';
                } else {
                    model = '';
                }

                legendHtml.push('    <li class="chart_legend on" style="color:' + currentData.borderColor + '" data-parts="' + partName + '">');
                legendHtml.push('		 <input type="hidden" name="partNumber" value="' + partName + '"/>');
                legendHtml.push('		 <input type="hidden" name="vdc" value="' + currentData.vdc + '"/>');
                legendHtml.push('		 <input type="hidden" name="degC" value="' + currentData.degC + '"/>');
                legendHtml.push('		 <input type="hidden" name="modelTypeOne" value="' + modelTypeOne + '"/>');
                legendHtml.push('        <a href="javascript:void(0);" class="chip" onclick="SEM.chart.setEventLegend(this, event, ' + '\'' + i + '\'' + ')"></a>');
                legendHtml.push('        <span class="parts_name">' + partName + ', ' + graphType + ', ' + vdc + ', ' + degC + ', ' + model + '</span>');
                legendHtml.push('        <button type="button" class="btn_remove" onclick="SEM.chart.removeLegend(this, event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ');">remove</button>');
                legendHtml.push('    </li>');
            }
            legendHtml.push('</ul>');

            return legendHtml.join('\n');
        }
    },
    'DCBias': {
        layerTitle: {
            backgroundColor: '#5984f4',
            title: function () {
                var result = '直流偏置电压特性';

                return result;
            }
        },
        axesType: {
            x: 'linear',
            y: 'linear'
        },
        axesRange: function (yData) {
            yData = yData || '';
            var result = {};

            if (yData === 'DeltaC') {
                result.y = {
                    min: -100,
                    max: 20,
                    stepSize: 20
                };
            }

            return result;
        },
        label: {
            x: 'DC Voltage(Vdc)',
            y: 'Capacitance(uF)'
        },
        tooltipLabel: function (tooltipItem, data) {
            var idx = tooltipItem.datasetIndex; // 해당 차트 라인
            var lineInfo = data.datasets[idx]; // 해당 차트 라인 정보
            var layerIdx = this._chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var dsDcSign = 'AC' + lineInfo.dsDcSign + 'Vrms';
            var dsDcFre = (lineInfo.dsDcFre / 1000) + 'kHz';
            var degC = lineInfo.degC + 'degC';
            var _digitX = parseFloat(Number(tooltipItem.xLabel).toFixed(5));
            var _digitY = parseFloat(Number(tooltipItem.yLabel).toFixed(5));
            var valueX = 'DC Bias: ' + _digitX + 'Vdc';
            var valueY = '';
            var asixYOptionOrigin = lineInfo.asixYOption; // 원본 구분 값 DeltaC, DeltaT
            var asixYString = ''; // asixYOption front용 텍스트

            if (asixYOptionOrigin === 'Capacitance') {
                valueY = 'Capacitance: ' + tooltipItem.yLabel.convertUnit('u', 'F', [5]);
                asixYString = 'Capacitance';
            } else if (asixYOptionOrigin === 'DeltaC') {
                valueY = 'ΔC: ' + _digitY + '%';
                asixYString = 'ΔC';
            }

            return [
                'DC Bias' + ', ' + asixYString,
                degC + ', ' + dsDcSign + ', ' + dsDcFre,
                valueX,
                valueY
            ];
        },
        legendCallback: function (chart) { // 범례 커스텀
            var legendHtml = [];
            var currentData, partName, subType, vdc, degC, modelType, model, asixYOptionOrigin, asixYString;
            var dataset = chart.data.datasets;
            var layerIdx = chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            // var graphType = thisLayerData.graphType;
            var graphType = 'DC Bias';

            legendHtml.push('<ul>');
            legendHtml.push('    <input type="hidden" id="saveDataGraphType' + layerIdx + '" name="graphType' + layerIdx + '" value="DCBias"/>');
            legendHtml.push('	 <input type="hidden" id="saveSimulationType' + layerIdx + '" name="simulationType' + layerIdx + '" value="CHAR"/>');
            for (var i = 0; i < dataset.length; i++) {
                currentData = dataset[i];
                partName = currentData.label;
                subType = currentData.graphSubType;
                vdc = currentData.vdc + 'Vdc';
                degC = currentData.degC + 'degC';
                modelType = currentData.modelType;
                dsDcSign = 'AC' + currentData.dsDcSign + 'Vrms';
                dsDcFre = (currentData.dsDcFre / 1000) + 'kHz';
                asixYOptionOrigin = currentData.asixYOption;

                if (asixYOptionOrigin === 'Capacitance') {
                    asixYString = 'Capacitance';
                } else if (asixYOptionOrigin === 'DeltaC') {
                    asixYString = 'ΔC';
                }

                if (modelType === 'Precise') {
                    model = modelType;
                } else if (modelType === 'Simple') {
                    model = '(C(F) ' + currentData.simC.toExponential(2) + ' / L(H) ' + currentData.simL.toExponential(2) + ' / R(Ω) ' + currentData.simR.toExponential(2) + ')';
                } else {
                    model = '';
                }

                legendHtml.push('    <li class="chart_legend on" style="color:' + currentData.borderColor + '" data-parts="' + partName + '" data-param-type="' + asixYOptionOrigin + '">');
                legendHtml.push('		 <input type="hidden" name="partNumber" value="' + partName + '"/>');
                legendHtml.push('        <a href="javascript:void(0);" class="chip" onclick="SEM.chart.setEventLegend(this, event, ' + '\'' + i + '\'' + ')"></a>');
                legendHtml.push('        <span class="parts_name">' + partName + ', ' + graphType + ', ' + asixYString + ', ' + degC + ', ' + dsDcSign + ', ' + dsDcFre + '</span>');
                legendHtml.push('        <button type="button" class="btn_remove" onclick="SEM.chart.removeLegend(this, event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ');">remove</button>');
                legendHtml.push('    </li>');
            }
            legendHtml.push('</ul>');

            return legendHtml.join('\n');
        },
        selectYData: function () {
            var data = {
                type: ['DeltaC', 'Capacitance'], // 배열 순서대로 노출
                title: {
                    Capacitance: 'Capacitance(uF)',
                    DeltaC: 'ΔC(%)'
                },
                display: true
            };

            return data;
        }
    },
    'ACVolt': {
        layerTitle: {
            backgroundColor: '#5984f4',
            title: function () {
                var result = '交流电压特性';

                return result;
            }
        },
        axesType: {
            x: 'linear',
            y: 'linear'
        },
        axesRange: function (yData) {
            yData = yData || '';
            var result = {};
            result.x = {
                min: 0,
                max: 2.5,
                stepSize: 0.5
            };

            if (yData === 'DeltaC') {
                result.y = {
                    min: -60,
                    max: 40,
                    stepSize: 20
                };
            }

            return result;
        },
        label: {
            x: 'AC Voltage(Vrms)',
            y: 'Capacitance(uF)'
        },
        tooltipLabel: function (tooltipItem, data) {
            var idx = tooltipItem.datasetIndex; // 해당 차트 라인
            var lineInfo = data.datasets[idx]; // 해당 차트 라인 정보
            var layerIdx = this._chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var vdc = lineInfo.vdc + 'Vdc';
            var degC = lineInfo.degC + 'degC';
            var dsDcFre = (lineInfo.dsDcFre / 1000) + 'kHz';
            var _digitX = parseFloat(Number(tooltipItem.xLabel).toFixed(5));
            var _digitY = parseFloat(Number(tooltipItem.yLabel).toFixed(5));
            var valueX = 'AC Volt.: ' + _digitX + 'Vrms';
            var valueY = '';
            var asixYOptionOrigin = lineInfo.asixYOption; // 원본 구분 값 DeltaC, DeltaT
            var asixYString = ''; // asixYOption front용 텍스트

            if (asixYOptionOrigin === 'Capacitance') {
                valueY = 'Capacitance: ' + tooltipItem.yLabel.convertUnit('u', 'F', [5]);
                asixYString = 'Capacitance';
            } else if (asixYOptionOrigin === 'DeltaC') {
                valueY = 'ΔC: ' + _digitY + '%';
                asixYString = 'ΔC';
            }

            return [
                'AC Volt.' + ', ' + asixYString,
                vdc + ', ' + degC + ', ' + dsDcFre,
                valueX,
                valueY
            ];
        },
        legendCallback: function (chart) { // 범례 커스텀
            var legendHtml = [];
            var currentData, partName, subType, vdc, degC, modelType, model;
            var dataset = chart.data.datasets;
            var layerIdx = chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var graphType = thisLayerData.graphType;

            legendHtml.push('<ul>');
            legendHtml.push('    <input type="hidden" id="saveDataGraphType' + layerIdx + '" name="graphType' + layerIdx + '" value="' + graphType + '"/>');
            legendHtml.push('	 <input type="hidden" id="saveSimulationType' + layerIdx + '" name="simulationType' + layerIdx + '" value="CHAR"/>');
            for (var i = 0; i < dataset.length; i++) {
                currentData = dataset[i];
                partName = currentData.label;
                subType = currentData.graphSubType;
                vdc = currentData.vdc + 'Vdc';
                degC = currentData.degC + 'degC';
                dsDcSign = 'AC' + currentData.dsDcSign + 'Vrms';
                dsDcFre = (currentData.dsDcFre / 1000) + 'kHz';
                asixYOptionOrigin = currentData.asixYOption;

                if (asixYOptionOrigin === 'Capacitance') {
                    asixYString = 'Capacitance';
                } else if (asixYOptionOrigin === 'DeltaC') {
                    asixYString = 'ΔC';
                }

                if (modelType === 'Precise') {
                    model = modelType;
                } else if (modelType === 'Simple') {
                    model = '(C(F) ' + currentData.simC.toExponential(2) + ' / L(H) ' + currentData.simL.toExponential(2) + ' / R(Ω) ' + currentData.simR.toExponential(2) + ')';
                } else {
                    model = '';
                }

                legendHtml.push('    <li class="chart_legend on" style="color:' + currentData.borderColor + '" data-parts="' + partName + '" data-param-type="' + asixYOptionOrigin + '">');
                legendHtml.push('		 <input type="hidden" name="partNumber" value="' + partName + '"/>');
                legendHtml.push('        <a href="javascript:void(0);" class="chip" onclick="SEM.chart.setEventLegend(this, event, ' + '\'' + i + '\'' + ')"></a>');
                legendHtml.push('        <span class="parts_name">' + partName + ', ' + graphType + ', ' + asixYString + ', ' + vdc + ', ' + degC + ', ' + dsDcFre + '</span>');
                legendHtml.push('        <button type="button" class="btn_remove" onclick="SEM.chart.removeLegend(this, event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ');">remove</button>');
                legendHtml.push('    </li>');
            }
            legendHtml.push('</ul>');

            return legendHtml.join('\n');
        },
        selectYData: function () {
            var data = {
                type: ['DeltaC', 'Capacitance'], // 배열 순서대로 노출
                title: {
                    Capacitance: 'Capacitance(uF)',
                    DeltaC: 'ΔC(%)'
                },
                display: true
            };

            return data;
        }
    },
    'RippleCurr': {
        layerTitle: {
            backgroundColor: '#5984f4',
            title: function () {
                var result = '温升(自热)';

                return result;
            }
        },
        axesType: {
            x: 'linear',
            y: 'logarithmic'
        },
        /**
         * @param {string} yData Y축 유형
         */
        axesRange: function (yData) {
            yData = yData || '';
            var result = {};

            // 1 미만 값이 존재 :: 2020-12-02
            // if (yData === 'DeltaT') {
            //     result.y = {
            //         min: 1
            //     };
            // }

            return result;
        },
        label: {
            x: 'Ripple Current(Arms)',
            y: 'ΔT(degC)'
        },
        tooltipLabel: function (tooltipItem, data) {
            var idx = tooltipItem.datasetIndex; // 해당 차트 라인
            var lineInfo = data.datasets[idx]; // 해당 차트 라인 정보
            var layerIdx = this._chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var _digitX = parseFloat(Number(tooltipItem.xLabel).toFixed(5));
            var _digitY = parseFloat(Number(tooltipItem.yLabel).toFixed(5));
            var valueX = 'Current:' + _digitX + 'Arms';
            var valueY = '';
            var asixY = '';
            var asixYOptionOrigin = lineInfo.asixYOption; // 원본 구분 값 DeltaC, DeltaT
            var asixYString = ''; // asixYOption front용 텍스트

            if (asixYOptionOrigin === 'Temperature') {
                valueY = 'Temperature: ' + _digitY + 'degC';
                asixYString = 'T(degC)';
            } else if (asixYOptionOrigin === 'DeltaT') {
                valueY = 'ΔT: ' + _digitY + 'degC';
                asixYString = 'ΔT(degC)';
            }

            return [
                'RippleCurr.' + ', ' + asixYString,
                'Frequency: ' + lineInfo.rippleFreq + 'kHz, ',
                valueX,
                valueY
            ];
        },
        legendCallback: function (chart) { // 범례 커스텀
            var legendHtml = [];
            var currentData, partName, vdc, degC, modelType, model, asixYOptionOrigin, asixYString;
            var dataset = chart.data.datasets;
            var layerIdx = chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var graphType = thisLayerData.graphType;

            legendHtml.push('<ul>');
            legendHtml.push('<input type="hidden" id="saveDataGraphType' + layerIdx + '" name="graphType' + layerIdx + '" value="' + graphType + '"/>');
            legendHtml.push('<input type="hidden" id="saveSimulationType' + layerIdx + '" name="simulationType' + layerIdx + '" value="CHAR"/>');

            for (var i = 0; i < dataset.length; i++) {
                currentData = dataset[i];
                partName = currentData.label;
                vdc = currentData.vdc + 'Vdc';
                degC = currentData.degC + 'degC';
                rippleFreq = currentData.rippleFreq + 'kHz';
                asixYOptionOrigin = currentData.asixYOption;

                if (asixYOptionOrigin === 'Temperature') {
                    asixYString = 'T';
                } else if (asixYOptionOrigin === 'DeltaT') {
                    asixYString = 'ΔT';
                }

                legendHtml.push('    <li class="chart_legend on" style="color:' + currentData.borderColor + '" data-parts="' + partName + '" data-param-type="' + asixYOptionOrigin + '">');
                legendHtml.push('		 <input type="hidden" name="partNumber" value="' + partName + '"/>');
                legendHtml.push('        <a href="javascript:void(0);" class="chip" onclick="SEM.chart.setEventLegend(this, event, ' + '\'' + i + '\'' + ')"></a>');
                legendHtml.push('        <span class="parts_name">' + partName + ', ' + 'RippleCurr.' + ', ' + asixYString + '(degC)' + ', ' + rippleFreq + '</span>');
                legendHtml.push('        <button type="button" class="btn_remove" onclick="SEM.chart.removeLegend(this, event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ');">remove</button>');
                legendHtml.push('    </li>');
            }
            legendHtml.push('</ul>');

            return legendHtml.join('\n');
        },
        selectYData: function () {
            var data = {
                type: ['DeltaT', 'Temperature'], // 배열 순서대로 노출
                title: {
                    Temperature: 'Temperature(degC)',
                    DeltaT: 'ΔT(degC)'
                },
                display: false
            };

            return data;
        }
    },
    'TCC': {
        layerTitle: {
            backgroundColor: '#5984f4',
            title: function () {
                var result = '室温温度特性';

                return result;
            }
        },
        axesType: {
            x: 'linear',
            y: 'linear'
        },
        axesRange: function (yData) {
            yData = yData || '';
            var result = {};

            if (yData === 'DeltaC') {
                result.y = {
                    min: -100,
                    max: 40,
                    stepSize: 20
                };
            }

            return result;
        },
        label: {
            x: 'Temperature(degC)',
            y: 'ΔC(%)'
        },
        tooltipLabel: function (tooltipItem, data) {
            var idx = tooltipItem.datasetIndex; // 해당 차트 라인
            var lineInfo = data.datasets[idx]; // 해당 차트 라인 정보
            var layerIdx = this._chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var vdc, subType, sign, fre;
            var _digitX = parseFloat(Number(tooltipItem.xLabel).toFixed(5));
            var _digitY = parseFloat(Number(tooltipItem.yLabel).toFixed(5));
            var valueX = 'Temperature: ' + _digitX + 'degC';
            var valueY = '';
            var asixYOptionOrigin = lineInfo.asixYOption; // 원본 구분 값 DeltaC, DeltaT
            var asixYString = ''; // asixYOption front용 텍스트

            if (asixYOptionOrigin === 'Capacitance') {
                valueY = 'Capacitance: ' + tooltipItem.yLabel.convertUnit('u', 'F', [5]);
                asixYString = 'Capacitance';
            } else if (asixYOptionOrigin === 'DeltaC') {
                valueY = 'ΔC: ' + _digitY + '%';
                asixYString = 'ΔC';
            }

            if (lineInfo.graphSubType === 'BiasTCC') {
                subType = 'Bias TCC';
                vdc = lineInfo.dsBiasVdc + 'Vdc';
                sign = 'AC' + lineInfo.dsDcSign + 'Vrms';
                fre = (lineInfo.dsDcFre / 1000) + 'kHz';
            } else {
                subType = lineInfo.graphSubType;
                vdc = lineInfo.vdc + 'Vdc';
                sign = 'AC' + lineInfo.dsTccSign + 'Vrms';
                fre = (lineInfo.dsTccFre / 1000) + 'kHz';
            }

            return [
                subType + ', ' + asixYString,
                vdc + ', ' + sign + ', ' + fre,
                valueX,
                valueY
            ];
        },
        legendCallback: function (chart) { // 범례 커스텀
            var legendHtml = [];
            var currentData, partName, subType, vdc, modelType, sign, fre, asixYOptionOrigin, asixYString;
            var dataset = chart.data.datasets;
            var layerIdx = chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var graphType = thisLayerData.graphType;

            legendHtml.push('<ul>');
            legendHtml.push('    <input type="hidden" id="saveDataGraphType' + layerIdx + '" name="graphType' + layerIdx + '" value="' + graphType + '"/>');
            legendHtml.push('	 <input type="hidden" id="saveSimulationType' + layerIdx + '" name="simulationType' + layerIdx + '" value="CHAR"/>');
            for (var i = 0; i < dataset.length; i++) {
                currentData = dataset[i];
                partName = currentData.label;
                degC = currentData.degC + 'degC';
                modelType = currentData.modelType;
                asixYOptionOrigin = currentData.asixYOption;

                if (asixYOptionOrigin === 'Capacitance') {
                    asixYString = 'Capacitance';
                } else if (asixYOptionOrigin === 'DeltaC') {
                    asixYString = 'ΔC';
                }

                if (currentData.graphSubType === 'BiasTCC') {
                    subType = 'Bias TCC';
                    vdc = currentData.dsBiasVdc + 'Vdc';
                    sign = 'AC' + currentData.dsDcSign + 'Vrms';
                    fre = (currentData.dsDcFre / 1000) + 'kHz';
                } else {
                    subType = currentData.graphSubType;
                    vdc = currentData.vdc + 'Vdc';
                    sign = 'AC' + currentData.dsTccSign + 'Vrms';
                    fre = (currentData.dsTccFre / 1000) + 'kHz';
                }

                if (modelType === 'Precise') {
                    model = modelType;
                } else if (modelType === 'Simple') {
                    model = '(C(F) ' + currentData.simC.toExponential(2) + ' / L(H) ' + currentData.simL.toExponential(2) + ' / R(Ω) ' + currentData.simR.toExponential(2) + ')';
                } else {
                    model = '';
                }

                legendHtml.push('    <li class="chart_legend on" style="color:' + currentData.borderColor + '" data-parts="' + partName + '" data-param-type="' + asixYOptionOrigin + '">');
                legendHtml.push('		 <input type="hidden" name="partNumber" value="' + partName + '"/>');
                legendHtml.push('        <a href="javascript:void(0);" class="chip" onclick="SEM.chart.setEventLegend(this, event, ' + '\'' + i + '\'' + ')"></a>');
                legendHtml.push('        <span class="parts_name">' + partName + ', ' + subType + ', ' + asixYString + ', ' + vdc + ', ' + sign + ', ' + fre + '</span>');
                legendHtml.push('        <button type="button" class="btn_remove" onclick="SEM.chart.removeLegend(this, event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ');">remove</button>');
                legendHtml.push('    </li>');
            }
            legendHtml.push('</ul>');

            return legendHtml.join('\n');
        },
        selectYData: function () {
            var data = {
                type: ['DeltaC', 'Capacitance'], // 배열 순서대로 노출
                title: {
                    Capacitance: 'Capacitance(uF)',
                    DeltaC: 'ΔC(%)'
                },
                display: true
            };

            return data;
        }
    },
    'AppliedV': {
        layerTitle: {
            backgroundColor: '#5984f4',
            title: function () {
                var result = '施加电压';

                return result;
            }
        },
        axesType: {
            x: 'logarithmic',
            y: 'logarithmic'
        },
        axesRange: function (yData) {
            yData = yData || '';
            var result = {};

            return result;
        },
        label: {
            x: 'Frequency(KHz)',
            y: 'Applied Voltage(Vp-p)'
        },
        tooltipLabel: function (tooltipItem, data) {
            var idx = tooltipItem.datasetIndex; // 해당 차트 라인
            var lineInfo = data.datasets[idx]; // 해당 차트 라인 정보
            var layerIdx = this._chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var vdc, subType, sign, fre;
            var graphTypeString = 'Applied Voltage';
            var _digitX = parseFloat(Number(tooltipItem.xLabel).toFixed(5));
            var _digitY = 0;
            var valueX = 'Frequency: ' + tooltipItem.xLabel + 'KHz';
            var valueY = graphTypeString+ ': '+ tooltipItem.yLabel + 'Vp-p';
            var asixYOptionOrigin = lineInfo.asixYOption; // 원본 구분 값 DeltaC, DeltaT
            var asixYString = ''; // asixYOption front용 텍스트
            
            vdc = "105degC";

            return [
                graphTypeString + ', ' + vdc,
                valueX,
                valueY
            ];
        },
        legendCallback: function (chart) { // 범례 커스텀
            var legendHtml = [];
            var currentData, partName, subType, vdc, modelType, sign, fre, asixYOptionOrigin, asixYString;
            var dataset = chart.data.datasets;
            var layerIdx = chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var graphType = thisLayerData.graphType;
            var graphTypeString = 'Applied Voltage';

            legendHtml.push('<ul>');
            legendHtml.push('    <input type="hidden" id="saveDataGraphType' + layerIdx + '" name="graphType' + layerIdx + '" value="' + graphType + '"/>');
            legendHtml.push('	 <input type="hidden" id="saveSimulationType' + layerIdx + '" name="simulationType' + layerIdx + '" value="CHAR"/>');
            for (var i = 0; i < dataset.length; i++) {
                currentData = dataset[i];
                partName = currentData.label;
                degC = currentData.degC + 'degC';
                modelType = currentData.modelType;

                if (modelType === 'Precise') {
                    model = modelType;
                } else if (modelType === 'Simple') {
                    model = '(C(F) ' + currentData.simC.toExponential(2) + ' / L(H) ' + currentData.simL.toExponential(2) + ' / R(Ω) ' + currentData.simR.toExponential(2) + ')';
                } else {
                    model = '';
                };

                vdc = "105degC";

                legendHtml.push('    <li class="chart_legend on" style="color:' + currentData.borderColor + '" data-parts="' + partName + '">');
                legendHtml.push('		 <input type="hidden" name="partNumber" value="' + partName + '"/>');
                legendHtml.push('        <a href="javascript:void(0);" class="chip" onclick="SEM.chart.setEventLegend(this, event, ' + '\'' + i + '\'' + ')"></a>');
                legendHtml.push('        <span class="parts_name">' + partName + ', ' + graphTypeString + ', ' + vdc + '</span>');
                legendHtml.push('        <button type="button" class="btn_remove" onclick="SEM.chart.removeLegend(this, event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ');">remove</button>');
                legendHtml.push('    </li>');
            }
            legendHtml.push('</ul>');

            return legendHtml.join('\n');
        }
    },
    'AppliedI': {
        layerTitle: {
            backgroundColor: '#5984f4',
            title: function () {
                var result = '施加电流';

                return result;
            }
        },
        axesType: {
            x: 'logarithmic',
            y: 'logarithmic'
        },
        axesRange: function (yData) {
            yData = yData || '';
            var result = {};

            // if (yData === 'DeltaC') {
            //     result.y = {
            //         min: -100,
            //         max: 40,
            //         stepSize: 20
            //     };
            // }

            return result;
        },
        label: {
            x: 'Frequency(KHz)',
            y: 'Applied Current(Arms)'
        },
        tooltipLabel: function (tooltipItem, data) {
            var idx = tooltipItem.datasetIndex; // 해당 차트 라인
            var lineInfo = data.datasets[idx]; // 해당 차트 라인 정보
            var layerIdx = this._chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var vdc, subType, sign, fre;
            var graphTypeString = 'Applied Current';
            var _digitX = parseFloat(Number(tooltipItem.xLabel).toFixed(5));
            var _digitY = 0;
            var valueX = 'Frequency: ' + tooltipItem.xLabel + 'KHz';
            var valueY = graphTypeString + ': '+ tooltipItem.yLabel + 'Arms';
            var asixYOptionOrigin = lineInfo.asixYOption; // 원본 구분 값 DeltaC, DeltaT
            var asixYString = ''; // asixYOption front용 텍스트
            
            vdc = "105degC";

            return [
                graphTypeString + ', ' + vdc,
                valueX,
                valueY
            ];
        },
        legendCallback: function (chart) { // 범례 커스텀
            var legendHtml = [];
            var currentData, partName, subType, vdc, modelType, sign, fre, asixYOptionOrigin, asixYString;
            var dataset = chart.data.datasets;
            var layerIdx = chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var graphType = thisLayerData.graphType;
            var graphTypeString = 'Applied Current';

            legendHtml.push('<ul>');
            legendHtml.push('    <input type="hidden" id="saveDataGraphType' + layerIdx + '" name="graphType' + layerIdx + '" value="' + graphType + '"/>');
            legendHtml.push('	 <input type="hidden" id="saveSimulationType' + layerIdx + '" name="simulationType' + layerIdx + '" value="CHAR"/>');
            for (var i = 0; i < dataset.length; i++) {
                currentData = dataset[i];
                partName = currentData.label;
                degC = currentData.degC + 'degC';
                modelType = currentData.modelType;

                if (modelType === 'Precise') {
                    model = modelType;
                } else if (modelType === 'Simple') {
                    model = '(C(F) ' + currentData.simC.toExponential(2) + ' / L(H) ' + currentData.simL.toExponential(2) + ' / R(Ω) ' + currentData.simR.toExponential(2) + ')';
                } else {
                    model = '';
                };

                vdc = "105degC";

                legendHtml.push('    <li class="chart_legend on" style="color:' + currentData.borderColor + '" data-parts="' + partName + '">');
                legendHtml.push('		 <input type="hidden" name="partNumber" value="' + partName + '"/>');
                legendHtml.push('        <a href="javascript:void(0);" class="chip" onclick="SEM.chart.setEventLegend(this, event, ' + '\'' + i + '\'' + ')"></a>');
                legendHtml.push('        <span class="parts_name">' + partName + ', ' + graphTypeString + ', ' + vdc + '</span>');
                legendHtml.push('        <button type="button" class="btn_remove" onclick="SEM.chart.removeLegend(this, event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ');">remove</button>');
                legendHtml.push('    </li>');
            }
            legendHtml.push('</ul>');

            return legendHtml.join('\n');
        }
    },
    'AppliedVI': {
        layerTitle: {
            backgroundColor: '#5984f4',
            title: function () {
                var result = '施加电压&电流';

                return result;
            }
        },
        axesType: {
            x: 'logarithmic',
            y: 'logarithmic'
        },
        axesPosition: function (subType) {
            subType = subType || '';
            var result = {};

            if (subType === 'AppliedV') {
                result.y = {
                    id: "left-axis",
                    min : 10,
                    max : 2000,
                    label : 'Applied Voltage(Vp-p)',
                    pos : 'left'
                };
            }else if(subType === 'AppliedI'){
                result.y = {
                    id: "right-axis",
                    min : 0.1,
                    max : 20,
                    label : 'Applied Current(Arms)',
                    pos : 'right'
                };
            };

            return result;
        },
        axesRange: function (yData) {
            yData = yData || '';
            var result = {};

            // if (yData === 'DeltaC') {
            //     result.y = {
            //         min: -100,
            //         max: 40,
            //         stepSize: 20
            //     };
            // }

            return result;
        },
        label: {
            x: 'Frequency(KHz)',
            y: 'Applied Voltage(Vp-p)',
        },
        tooltipLabel: function (tooltipItem, data) {
            var idx = tooltipItem.datasetIndex; // 해당 차트 라인
            var lineInfo = data.datasets[idx]; // 해당 차트 라인 정보
            var layerIdx = this._chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var vdc, subType, sign, fre;
            var _digitX = parseFloat(Number(tooltipItem.xLabel).toFixed(5));
            var _digitY = 0;
            var valueX = 'Frequency: ' + tooltipItem.xLabel + 'KHz';

            vdc = "105degC";

            if (lineInfo.graphSubType === 'AppliedV') {
                var graphTypeString = 'Applied Voltage';
                var valueY = graphTypeString + ': '+ tooltipItem.yLabel + 'Vp-p';
            }else if(lineInfo.graphSubType === 'AppliedI'){
                var graphTypeString = 'Applied Current';
                var valueY = graphTypeString + ': '+ tooltipItem.yLabel + 'Arms';
            };

            return [
                graphTypeString + ', ' + vdc,
                valueX,
                valueY
            ];
        },
        legendCallback: function (chart) { // 범례 커스텀
            var legendHtml = [];
            var currentData, partName, subType, vdc, modelType, sign, fre, asixYOptionOrigin, asixYString, graphTypeString;
            var dataset = chart.data.datasets;
            var layerIdx = chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var graphType = thisLayerData.graphType;

            legendHtml.push('<ul>');
            legendHtml.push('    <input type="hidden" id="saveDataGraphType' + layerIdx + '" name="graphType' + layerIdx + '" value="' + graphType + '"/>');
            legendHtml.push('	 <input type="hidden" id="saveSimulationType' + layerIdx + '" name="simulationType' + layerIdx + '" value="CHAR"/>');
            for (var i = 0; i < dataset.length; i++) {
                currentData = dataset[i];
                partName = currentData.label;
                degC = currentData.degC + 'degC';
                modelType = currentData.modelType;

                if (currentData.graphSubType === 'AppliedV') {
                    graphTypeString = 'Applied Voltage';
                }else if(currentData.graphSubType === 'AppliedI'){
                    graphTypeString = 'Applied Current';
                };
                

                if (modelType === 'Precise') {
                    model = modelType;
                } else if (modelType === 'Simple') {
                    model = '(C(F) ' + currentData.simC.toExponential(2) + ' / L(H) ' + currentData.simL.toExponential(2) + ' / R(Ω) ' + currentData.simR.toExponential(2) + ')';
                } else {
                    model = '';
                };

                vdc = "105degC";

                legendHtml.push('    <li class="chart_legend on" style="color:' + currentData.borderColor + '" data-parts="' + partName + '">');
                legendHtml.push('		 <input type="hidden" name="partNumber" value="' + partName + '"/>');
                legendHtml.push('        <a href="javascript:void(0);" class="chip" onclick="SEM.chart.setEventLegend(this, event, ' + '\'' + i + '\'' + ')"></a>');
                legendHtml.push('        <span class="parts_name">' + partName + ', ' + graphTypeString + ', ' + vdc + '</span>');
                legendHtml.push('        <button type="button" class="btn_remove" onclick="SEM.chart.removeLegend(this, event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ');">remove</button>');
                legendHtml.push('    </li>');
            }
            legendHtml.push('</ul>');

            return legendHtml.join('\n');
        }
    },
    'DCBiasByTemp': {
        layerTitle: {
            backgroundColor: '#a860e0',
            title: function () {
                var result = '直流偏置电压特性';

                return result;
            }
        },
        axesType: {
            x: 'linear',
            y: 'linear'
        },
        axesRange: function (yData, maxData) {
            yData = yData || '';
            maxData = maxData || '';

            var result = {};
            
            if(maxData['x'] > 40){
                result.x = {
                    min: 0,
                    max: 40,
                    stepSize: 10
                };
            };
            if (yData === 'DeltaC') {
                result.y = {
                    min: -100,
                    max: 20,
                    stepSize: 20
                };
            }

            return result;
        },
        label: {
            x: 'DC volatage(Vdc)',
            y: 'Capacitance(uF)'
        },
        tooltipLabel: function (tooltipItem, data) {
            var idx = tooltipItem.datasetIndex; // 해당 차트 라인
            var lineInfo = data.datasets[idx]; // 해당 차트 라인 정보
            var layerIdx = this._chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var degC = lineInfo.degC + 'degC';
            var tccSign = 'AC' + lineInfo.tccSign + 'Vrms';
            var tccFreq = (lineInfo.tccFreq / 1000) + 'kHz';
            var _digitX = parseFloat(Number(tooltipItem.xLabel).toFixed(5));
            var _digitY = parseFloat(Number(tooltipItem.yLabel).toFixed(5));
            var valueX = 'DC Bias: ' + _digitX + 'Vdc';
            var valueY = '';
            var asixYOptionOrigin = lineInfo.asixYOption; // 원본 구분 값 DeltaC, DeltaT
            var asixYString = ''; // asixYOption front용 텍스트


            if (asixYOptionOrigin === 'Capacitance') {
                valueY = 'Capacitance: ' + tooltipItem.yLabel.convertUnit('u', 'F', [5]);
                asixYString = 'Capacitance';
            } else if (asixYOptionOrigin === 'DeltaC') {
                valueY = 'ΔC: ' + _digitY + '%';
                asixYString = 'ΔC';
            }

            return [
                'DC Bias @ temp' + ', ' + asixYString,
                degC + ', ' + tccSign + ', ' + tccFreq,
                valueX,
                valueY
            ];
        },
        legendCallback: function (chart) { // 범례 커스텀
            var legendHtml = [];
            var currentData, partName, subType, vdc, degC, modelType, model, asixYOptionOrigin, asixYString;
            var dataset = chart.data.datasets;
            var layerIdx = chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var graphType = thisLayerData.graphType;

            legendHtml.push('<ul>');
            legendHtml.push('    <input type="hidden" id="saveDataGraphType' + layerIdx + '" name="graphType' + layerIdx + '" value="' + graphType + '"/>');
            legendHtml.push('	 <input type="hidden" id="saveSimulationType' + layerIdx + '" name="simulationType' + layerIdx + '" value="TCCDC"/>');
            for (var i = 0; i < dataset.length; i++) {
                currentData = dataset[i];
                partName = currentData.label;
                subType = currentData.graphSubType;
                vdc = currentData.vdc + 'Vdc';
                degC = currentData.degC + 'degC';
                modelType = currentData.modelType;
                tccSign = 'AC' + currentData.tccSign + 'Vrms';
                tccFreq = (currentData.tccFreq / 1000) + 'kHz';
                asixYOptionOrigin = currentData.asixYOption;

                if (asixYOptionOrigin === 'Capacitance') {
                    asixYString = 'Capacitance';
                } else if (asixYOptionOrigin === 'DeltaC') {
                    asixYString = 'ΔC';
                }

                if (modelType === 'Precise') {
                    model = modelType;
                } else if (modelType === 'Simple') {
                    model = '(C(F) ' + currentData.simC.toExponential(2) + ' / L(H) ' + currentData.simL.toExponential(2) + ' / R(Ω) ' + currentData.simR.toExponential(2) + ')';
                } else {
                    model = '';
                }

                legendHtml.push('    <li class="chart_legend on" style="color:' + currentData.borderColor + '" data-parts="' + partName + '" data-param-type="' + asixYOptionOrigin + '">');
                legendHtml.push('		 <input type="hidden" name="partNumber" value="' + partName + '"/>');
                legendHtml.push('		 <input type="hidden" name="degC" value="' + currentData.degC + '"/>');
                legendHtml.push('        <a href="javascript:void(0);" class="chip" onclick="SEM.chart.setEventLegend(this, event, ' + '\'' + i + '\'' + ')"></a>');
                legendHtml.push('        <span class="parts_name">' + partName + ', ' + 'DC Bias @ temp' + ', ' + asixYString + ', ' + degC + ', ' + tccSign + ', ' + tccFreq + '</span>');
                legendHtml.push('        <button type="button" class="btn_remove" onclick="SEM.chart.removeLegend(this, event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ');">remove</button>');
                legendHtml.push('    </li>');
            }
            legendHtml.push('</ul>');

            return legendHtml.join('\n');
        },
        selectYData: function () {
            var data = {
                type: ['Capacitance', 'DeltaC'], // 배열 순서대로 노출
                title: {
                    Capacitance: 'Capacitance(uF)',
                    DeltaC: 'ΔC(%)'
                },
                display: true
            };

            return data;
        }
    },
    'TCCbyDC': {
        layerTitle: {
            backgroundColor: '#a860e0',
            title: function () {
                var result = '室温温度特性';

                return result;
            }
        },
        axesType: {
            x: 'linear',
            y: 'linear'
        },
        axesRange: function (yData) {
            yData = yData || '';
            var result = {};

            if (yData === 'DeltaC') {
                result.y = {
                    min: -100,
                    max: 40,
                    stepSize: 20
                };
            }

            return result;
        },
        label: {
            x: 'Temperature(degC)',
            y: 'Capacitance(uF)'
        },
        tooltipLabel: function (tooltipItem, data) {
            var idx = tooltipItem.datasetIndex; // 해당 차트 라인
            var lineInfo = data.datasets[idx]; // 해당 차트 라인 정보
            var layerIdx = this._chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var tccSign = 'AC' + lineInfo.tccSign + 'Vrms';
            var tccFreq = (lineInfo.tccFreq / 1000) + 'kHz';
            var vdc = lineInfo.vdc + 'Vdc';
            var degC = lineInfo.degC + 'degC';
            var _digitX = parseFloat(Number(tooltipItem.xLabel).toFixed(5));
            var _digitY = parseFloat(Number(tooltipItem.yLabel).toFixed(5));
            var valueX = 'Temperature: ' + _digitX + 'degC';
            var valueY = '';
            var asixYOptionOrigin = lineInfo.asixYOption; // 원본 구분 값 DeltaC, deltaT
            var asixYString = ''; // asixYOption front용 텍스트

            if (asixYOptionOrigin === 'Capacitance') {
                valueY = 'Capacitance: ' + tooltipItem.yLabel.convertUnit('u', 'F', [5]);
                asixYString = 'Capacitance';
            } else if (asixYOptionOrigin === 'DeltaC') {
                valueY = 'ΔC: ' + _digitY + '%';
                asixYString = 'ΔC';
            }

            return [
                'TCC @ DC(V)' + ', ' + asixYString,
                vdc + ', ' + tccSign + ', ' + tccFreq,
                valueX,
                valueY
            ];
        },
        legendCallback: function (chart) { // 범례 커스텀
            var legendHtml = [];
            var currentData, partName, subType, vdc, degC, modelType, model, asixYOptionOrigin, asixYString;
            var dataset = chart.data.datasets;
            var layerIdx = chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var graphType = thisLayerData.graphType;

            legendHtml.push('<ul>');
            legendHtml.push('    <input type="hidden" id="saveDataGraphType' + layerIdx + '" name="graphType' + layerIdx + '" value="' + graphType + '"/>');
            legendHtml.push('	 <input type="hidden" id="saveSimulationType' + layerIdx + '" name="simulationType' + layerIdx + '" value="TCCDC"/>');
            for (var i = 0; i < dataset.length; i++) {
                currentData = dataset[i];
                partName = currentData.label;
                subType = currentData.graphSubType;
                vdc = currentData.vdc + 'Vdc';
                degC = currentData.degC + 'degC';
                modelType = currentData.modelType;
                tccSign = 'AC' + currentData.tccSign + 'Vrms';
                tccFreq = (currentData.tccFreq / 1000) + 'kHz';

                asixYOptionOrigin = currentData.asixYOption;

                if (asixYOptionOrigin === 'Capacitance') {
                    asixYString = 'Capacitance';
                } else if (asixYOptionOrigin === 'DeltaC') {
                    asixYString = 'ΔC';
                }

                if (modelType === 'Precise') {
                    model = modelType;
                } else if (modelType === 'Simple') {
                    model = '(C(F) ' + currentData.simC.toExponential(2) + ' / L(H) ' + currentData.simL.toExponential(2) + ' / R(Ω) ' + currentData.simR.toExponential(2) + ')';
                } else {
                    model = '';
                }

                legendHtml.push('    <li class="chart_legend on" style="color:' + currentData.borderColor + '" data-parts="' + partName + '" data-param-type="' + asixYOptionOrigin + '">');
                legendHtml.push('		 <input type="hidden" name="partNumber" value="' + partName + '"/>');
                legendHtml.push('		 <input type="hidden" name="vdc" value="' + currentData.vdc + '"/>');
                legendHtml.push('        <a href="javascript:void(0);" class="chip" onclick="SEM.chart.setEventLegend(this, event, ' + '\'' + i + '\'' + ')"></a>');
                legendHtml.push('        <span class="parts_name">' + partName + ', ' + 'TCC @ DC(V)' + ', ' + asixYString + ', ' + vdc + ', ' + tccSign + ', ' + tccFreq + '</span>');
                legendHtml.push('        <button type="button" class="btn_remove" onclick="SEM.chart.removeLegend(this, event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ');">remove</button>');
                legendHtml.push('    </li>');
            }
            legendHtml.push('</ul>');

            return legendHtml.join('\n');
        },
        selectYData: function () {
            var data = {
                type: ['Capacitance', 'DeltaC'], // 배열 순서대로 노출
                title: {
                    Capacitance: 'Capacitance(uF)',
                    DeltaC: 'ΔC(%)'
                },
                display: true
            };

            return data;
        }
    },
    'SDB': {
        layerTitle: {
            backgroundColor: '#006cb1',
            title: function () {
                var result;
                var data = SEM.chart.tempInfo;
                var sParamCircuit = data.sParamCircuit;
                if(sParamCircuit == 'Series'){
                    sParamCircuit = 'Series';
                }else if(sParamCircuit == 'Shunt'){
                    sParamCircuit = 'Shunt';
                };
                result = 'S参数幅值' + ' (' + sParamCircuit + ')';

                return result;
            }
        },
        axesType: {
            x: 'logarithmic',
            y: 'linear'
        },
        label: {
            x: 'Frequency(MHz)',
            y: 'dB'
        },
        tooltipLabel: function (tooltipItem, data) {
            var idx = tooltipItem.datasetIndex; // 해당 차트 라인
            var lineInfo = data.datasets[idx]; // 해당 차트 라인 정보
            var layerIdx = this._chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var vdc = lineInfo.vdc + 'Vdc';
            var degC = lineInfo.degC + 'degC';
            var _digitX = parseFloat(Number(tooltipItem.xLabel).toFixed(5));
            var _digitY = parseFloat(Number(tooltipItem.yLabel).toFixed(5));

            return [
                lineInfo.sParamType,
                vdc + ', ' + degC + ', ' + lineInfo.sParamCircuit + ', ' + lineInfo.modelType,
                'Frequency: ' + tooltipItem.xLabel.convertUnit('M', 'Hz', [5]),
                lineInfo.sParamType + ': ' + _digitY + 'dB'
            ];
        },
        legendCallback: function (chart) { // 범례 커스텀
            var legendHtml = [];
            var currentData, partName, sParamType, vdc, degC, sParamCircuit, modelType, model;
            var dataset = chart.data.datasets;
            var layerIdx = chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var graphType = thisLayerData.graphType;

            legendHtml.push('<ul>');
            legendHtml.push('    <input type="hidden" id="saveDataGraphType' + layerIdx + '" name="graphType' + layerIdx + '" value="' + graphType + '"/>');
            legendHtml.push('	 <input type="hidden" id="saveSimulationType' + layerIdx + '" name="simuationType' + layerIdx + '" value="TEMPDC"/>');
            legendHtml.push('	 <input type="hidden" id="savesParamCircuit' + layerIdx + '" name="sParamCircuit' + layerIdx + '" value="' + dataset[0].sParamCircuit + '"/>');
            for (var i = 0; i < dataset.length; i++) {
                currentData = dataset[i];
                partName = currentData.label;
                vdc = currentData.vdc + 'Vdc';
                degC = currentData.degC + 'degC';
                sParamType = currentData.sParamType;
                sParamCircuit = currentData.sParamCircuit;
                modelType = currentData.modelType;

                if (modelType === 'Precise') {
                    model = modelType;
                    modelTypeOne = 'P';
                } else if (modelType === 'Simple') {
                    model = '(C(F) ' + currentData.simC.toExponential(2) + ' / L(H) ' + currentData.simL.toExponential(2) + ' / R(Ω) ' + currentData.simR.toExponential(2) + ')';
                    modelTypeOne = 'S';
                } else {
                    model = '';
                }

                legendHtml.push('    <li class="chart_legend on" style="color:' + currentData.borderColor + '" data-parts="' + partName + '" data-param-type="' + sParamType + '">');
                legendHtml.push('		 <input type="hidden" name="partNumber" value="' + partName + '"/>');
                legendHtml.push('		 <input type="hidden" name="vdc" value="' + currentData.vdc + '"/>');
                legendHtml.push('		 <input type="hidden" name="degC" value="' + currentData.degC + '"/>');
                legendHtml.push('		 <input type="hidden" name="modelTypeOne" value="' + modelTypeOne + '"/>');
                legendHtml.push('        <a href="javascript:void(0);" class="chip" onclick="SEM.chart.setEventLegend(this, event, ' + '\'' + i + '\'' + ')"></a>');
                legendHtml.push('        <span class="parts_name">' + partName + ', ' + 'S[dB]' + ', ' + sParamType + ', ' + vdc + ', ' + degC + ', ' + sParamCircuit + ', ' + model + '</span>');
                legendHtml.push('        <button type="button" class="btn_remove" onclick="SEM.chart.removeLegend(this, event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ');">remove</button>');
                legendHtml.push('    </li>');
            }
            legendHtml.push('</ul>');

            return legendHtml.join('\n');
        },
        selectYData: function () {
            var data = {
                type: ['S11', 'S21', 'S12', 'S22'], // 배열 순서대로 노출
                title: {
                    S11: 'S11(dB)',
                    S21: 'S21(dB)',
                    S12: 'S12(dB)',
                    S22: 'S22(dB)'
                },
                display: true
            };

            return data;
        }
    },
    'Smithchart': {
        layerTitle: {
            backgroundColor: '#006cb1',
            title: function () {
                var result;
                var data = SEM.chart.tempInfo;
                var sParamCircuit = data.sParamCircuit;
                if(sParamCircuit == 'Series'){
                    sParamCircuit = 'Series';
                }else if(sParamCircuit == 'Shunt'){
                    sParamCircuit = 'Shunt';
                };
                result = '史密斯圆图' + ' (' + sParamCircuit + ')';

                return result;
            }
        },
        axesType: {
            x: 'linear',
            y: 'linear'
        },
        label: {
            x: 'Frequency(MHz)',
            y: 'Capacitance(uF)'
        },
        tooltipLabel: function (tooltipItem, data) {
            var idx = tooltipItem.datasetIndex; // 해당 차트 라인
            var pointIdx = tooltipItem.index;
            var lineInfo = data.datasets[idx]; // 해당 차트 라인 정보
            var pointInfo = lineInfo.data[pointIdx]; // 해당 차트 라인 정보
            var layerIdx = this._chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var _digitX = parseFloat(Number(tooltipItem.xLabel).toFixed(5));
            var _digitY = parseFloat(Number(tooltipItem.yLabel).toFixed(5));
            var vdc = lineInfo.vdc + 'Vdc';
            var degC = lineInfo.degC + 'degC';
            var freq = Number(pointInfo.f).convertUnit('M', 'Hz', [5]);
            var mag = parseFloat(Number(pointInfo.m).toFixed(5)) + '∠';
            var phase = parseFloat(Number(pointInfo.p).toFixed(5));
            var real = parseFloat(Number(pointInfo.x).toFixed(5));

            var imagSymbol = setSymbol(pointInfo.y);

            var imag = imagSymbol + 'j' + Math.abs(Math.floor(pointInfo.y * 100000) / 100000); // j앞으로 계산 기호 위치 (계산기호 + 'j' + 절대값imag)
            var func = '=' + real + imag;
            var clr = 'Z=Z0*(' + pointInfo.z + ')'; // 계산된 값을 string으로 전달 받음 2018-11-09 (키값 = z)

            function sign(value) {
                value = +value;
                if (value === 0 || isNaN(value)) {
                    return Number(value);
                }
                return value > 0 ? 1 : -1;
            }

            function setSymbol(value) {
                var symbol;
                if (sign(value) === 1 || sign(value) === 0) {
                    symbol = '+';
                } else if (sign(value) === -1) {
                    symbol = '-';
                } else {
                    symbol = '';
                }

                return symbol;
            }

            return [
                vdc + ', ' + degC + ', ' + lineInfo.sParamCircuit + ', ' + lineInfo.modelType,
                'Frequency: ' + freq,
                lineInfo.sParamType + '=' + mag + phase,
                func,
                clr
            ];
        },
        legendCallback: function (chart) { // 범례 커스텀
            var legendHtml = [];
            var currentData, partName, sParamType, vdc, degC, sParamCircuit, modelType, model;
            var dataset = chart.data.datasets;
            var layerIdx = chart.id + 1; // 해당 레이어 번호
            var thisLayerData = SEM.chart.chartOriginData[layerIdx]; // 해당 차트 원본 데이터
            var graphType = thisLayerData.graphType;

            legendHtml.push('<ul>');
            legendHtml.push('    <input type="hidden" id="saveDataGraphType' + layerIdx + '" name="graphType' + layerIdx + '" value="' + graphType + '"/>');
            legendHtml.push('	 <input type="hidden" id="saveSimulationType' + layerIdx + '" name="simulationType' + layerIdx + '" value="TEMPDC"/>');
            legendHtml.push('	 <input type="hidden" id="savesParamCircuit' + layerIdx + '" name="sParamCircuit' + layerIdx + '" value="' + dataset[0].sParamCircuit + '"/>');
            for (var i = 0; i < dataset.length; i++) {
                currentData = dataset[i];
                partName = currentData.label;
                vdc = currentData.vdc + 'Vdc';
                degC = currentData.degC + 'degC';
                sParamType = currentData.sParamType;
                sParamCircuit = currentData.sParamCircuit;
                modelType = currentData.modelType;

                if (modelType === 'Precise') {
                    model = modelType;
                    modelTypeOne = 'P';
                } else if (modelType === 'Simple') {
                    model = '(C(F) ' + currentData.simC.toExponential(2) + ' / L(H) ' + currentData.simL.toExponential(2) + ' / R(Ω) ' + currentData.simR.toExponential(2) + ')';
                    modelTypeOne = 'S';
                } else {
                    model = '';
                }

                legendHtml.push('    <li class="chart_legend on" style="color:' + currentData.borderColor + '" data-parts="' + partName + '" data-param-type="' + sParamType + '">');
                legendHtml.push('		 <input type="hidden" name="partNumber" value="' + partName + '"/>');
                legendHtml.push('		 <input type="hidden" name="vdc" value="' + currentData.vdc + '"/>');
                legendHtml.push('		 <input type="hidden" name="degC" value="' + currentData.degC + '"/>');
                legendHtml.push('		 <input type="hidden" name="modelTypeOne" value="' + modelTypeOne + '"/>');
                legendHtml.push('        <a href="javascript:void(0);" class="chip" onclick="SEM.chart.setEventLegend(this, event, ' + '\'' + i + '\'' + ')"></a>');
                legendHtml.push('        <span class="parts_name">' + partName + ', ' + 'SmithChart' + ', ' + sParamType + ', ' + vdc + ', ' + degC + ', ' + sParamCircuit + ', ' + model + '</span>');
                legendHtml.push('        <button type="button" class="btn_remove" onclick="SEM.chart.removeLegend(this, event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ');">remove</button>');
                legendHtml.push('    </li>');
            }
            legendHtml.push('</ul>');

            return legendHtml.join('\n');
        },
        selectYData: function () {
            var data = {
                type: ['S11', 'S22'], // 배열 순서대로 노출
                title: {
                    S11: 'S11(dB)',
                    S22: 'S22(dB)'
                },
                display: true
            };

            return data;
        }
    }
};

SEM.chart.preventUnChecked('modelTypeList');