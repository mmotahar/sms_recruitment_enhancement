odoo.define('iot.widgets', function (require) {
"use strict";

var core = require('web.core');
var Widget = require('web.Widget');
var registry = require('web.field_registry');
var widget_registry = require('web.widget_registry');
var Dialog = require('web.Dialog');

var py_eval = require('web.py_utils').py_eval;
var _t = core._t;

var ActionManager = require('web.ActionManager');
ActionManager.include({
    _executeReportAction: function (action, options) {
        if (action.device_id) {
            // Call new route that sends you report to send to printer
            var self = this;
            self.action = action;
            return this._rpc({
                model: 'ir.actions.report',
                method: 'iot_render',
                args: [action.id, action.context.active_ids, {'device_id': action.device_id}]
            }).then(function (result) {
                var data = {
                    action: 'print',
                    type: result[1],
                    data: result[2]
                };
                return $.ajax({ //code from hw_screen pos
                    type: 'POST',
                    url: result[0],
                    dataType: 'json',
                    beforeSend: function (xhr) {
                        xhr.setRequestHeader('Content-Type', 'application/json');
                    },
                    data: JSON.stringify(data),
                    success: function (data) {
                        self.do_notify(_t('Successfully sent to printer!'));
                        return options.on_close();
                    },
                    error: function (data) {
                        self.do_warn(_t('Connection with the IoT Box failed!'));
                    },

                });
            });
        }
        else {
            return this._super.apply(this, arguments);
        }
    }
});

var IotDetectButton = Widget.extend({
    tagName: 'button',
    className: 'o_iot_detect_button btn btn-primary',
    events: {
        'click': '_onButtonClick',
    },
    init: function (parent, record) {
        this._super.apply(this, arguments);
        this.token = record.data.token;
        this.parallelRPC = 8;
        this.parseURL = new URL(window.location.href);
        this.controlImage = 'iot.jpg';
    },

    start: function () {
        this._super.apply(this, arguments);
        this.$el.text(_t('SCAN'));
    },

    _getUserIP: function (onNewIP) {
        //  onNewIp - your listener function for new IPs
        //compatibility for firefox and chrome
        var myPeerConnection = window.RTCPeerConnection || window.mozRTCPeerConnection || window.webkitRTCPeerConnection;
        var pc = new myPeerConnection({
            iceServers: []
        });
        var noop = function () {};
        var localIPs = {};
        var ipRegex = /([0-9]{1,3}(\.[0-9]{1,3}){3}|[a-f0-9]{1,4}(:[a-f0-9]{1,4}){7})/g;

        function iterateIP(ip) {
            if (!localIPs[ip]){
                if (ip.length < 16){
                    localIPs[ip] = true;
                    onNewIP(ip);
                }
            }
        }

        //create a bogus data channel
        pc.createDataChannel("");

        // create offer and set local description
        pc.createOffer().then(function (sdp) {
            sdp.sdp.split('\n').forEach(function (line) {
                if (line.indexOf('candidate') < 0) return;
                line.match(ipRegex).forEach(iterateIP);
            });

            pc.setLocalDescription(sdp, noop, noop);
        });

        //listen for candidate events
        pc.onicecandidate = function (ice) {
            if (!ice || !ice.candidate || !ice.candidate.candidate || !ice.candidate.candidate.match(ipRegex)) return;
            ice.candidate.candidate.match(ipRegex).forEach(iterateIP);
        };
    },

    _createThread: function (urls, range) {
        var self = this;
        var img = new Image();
        var url = urls.shift();

        if (url){
            $.ajax({
                url: url + '/hw_proxy/hello',
                method: 'GET',
                timeout: 400,
            }).done(function () {
                self._addIOT(url);
                self._connectToIOT(url);
                if (range) self._updateRangeProgress(range);
            }).fail(function (jqXHR, textStatus) {
                /*
                * If the request to /hw_proxy/hello returns an error while we contacted it in https,
                * it could mean the server certificate is not yet accepted by the client.
                * To know if it is really the case, we try to fetch an image on the http port of the server.
                * If it loads successfully, we call _addIOTWithCertificateError that will display an explicit error to the customer.
                */
                if (textStatus==='error' && self.parseURL.protocol === 'https:'){
                    var imgSrc = url + '/' + self.controlImage
                    img.src = imgSrc.replace('https://', 'http://');
                    img.onload = function() {
                        self._addIOTWithCertificateError(url);
                    };
                }
                self._createThread(urls, range);
                if (range) self._updateRangeProgress(range);
            });
        }
    },

    _addIPRange: function (range){
        var ipPerRange = 256;

        var $range = $('<li/>').addClass('list-group-item').append('<b>' + range + '*' + '</b>');
        var $progress = $('<div class="progress"/>');
        var $bar = $('<div class="progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"/>').css('width', '0%').text('0%');

        $progress.append($bar);
        $range.append($progress);

        this.ranges[range] = {
            $range: $range,
            $bar: $bar,
            urls: [],
            current: 0,
            total: ipPerRange,
        };
        this.$progressRanges.append($range);

        for (var i = 0; i < ipPerRange; i++) {
            var port = '';
            if(this.parseURL.protocol == 'http:'){
                port = ':8069';
            }
            this.ranges[range].urls.push(this.parseURL.protocol + '//' + (range + i) + port);
        }
    },

    _processIRRange: function (range){
        var len = Math.min(this.parallelRPC, range.urls.length);
        for (var i = 0; i < len; i++) {
            this._createThread(range.urls, range);
        }
    },

    _updateRangeProgress: function (range) {
        range.current ++;
        var percent = Math.round(range.current / range.total * 100);
        range.$bar.css('width', percent + '%').attr('aria-valuenow', percent).text(percent + '%');
    },

    _findIOTs: function (options) {
        options = options || {};
        var self = this;
        var range;

        this._getUserIP(function (ip) {
            self._initProgress();

            // Query localhost
            var local_url = self.parseURL.protocol + '//localhost:' + self.parseURL.port;
            self._createThread([local_url]);

            if (ip) {
                range = ip.replace(ip.split('.')[3], '');
                self._addIPRange(range);
            }
            else {
                self._addIPRange('192.168.0.');
                self._addIPRange('192.168.1.');
                self._addIPRange('10.0.0.');
            }

            _.each(self.ranges, self._processIRRange, self);
        });
    },

    _initProgress: function (){
        this.$progressBlock = $('.scan_progress').show();
        this.$progressRanges = this.$progressBlock.find('.scan_ranges').empty();
        this.$progressFound = this.$progressBlock.find('.found_devices').empty();

        this.ranges = {};
        this.iots = {};
    },

    _addIOT: function (url){
        var $iot = $('<li/>')
            .addClass('list-group-item')
            .appendTo(this.$progressFound);

        $('<a/>')
            .attr('href', url)
            .attr('target', '_blank')
            .text(url)
            .appendTo($iot);

        $iot.append('<i class="iot-scan-status-icon"/>')
            .append('<div class="iot-scan-status-msg"/>');

        this.iots[url] = $iot;
        this.$progressFound.append($iot);
    },

    _addIOTWithCertificateError: function (url){
        this._addIOT(url);
        var content = '<p>' + _t("Connection refused, please accept the certificate and restart the scan:")
                + '<ol class="pl-3 small">'
                    + '<li>' + _t('Click on the link above to open your IoT Homepage') + '</li>'
                    + '<li>' + _t('Click on Advanced/Show Details/Details/More information') + '</li>'
                    + '<li>' + _t('Click on Proceed to .../Add Exception/Visit this website/Go on to the webpage') + '</li>'
                    + '<li>' + _t('Firefox only: Click on Confirm Security Exception') + '</li>'
                    + '<li>' + _t('Restart SCAN') + '</li>'
                + '</ol>'
            + '</p>';
        this._updateIOT(url, 'error', content);
    },

    _updateIOT: function (url, status, message){
        if (this.iots[url]){
            var $iot = this.iots[url];
            var $icon = $iot.find('.iot-scan-status-icon');
            var $msg = $iot.find('.iot-scan-status-msg');

            var icon = 'fa pull-right iot-scan-status-icon mt-1 ';
            switch (status) {
                case "loading":
                    icon += 'fa-spinner fa-spin';
                    break;
                case "success":
                    icon += "fa-check text-success";
                    break;
                default:
                    icon += "fa-exclamation-triangle text-danger";
            }

            $icon.removeClass().addClass(icon);
            $msg.empty().append(message);
        }
    },

    _connectToIOT: function (url){
        var self = this;
        var full_url = url + '/hw_drivers/box/connect';
        var json_data = {token: self.token};

        this._updateIOT(url, 'loading', _t('Pairing with IoT...'));

        $.ajax({
            headers: {'Content-Type': 'application/json'},
            url: full_url,
            dataType: 'json',
            data: JSON.stringify(json_data),
            type: 'POST',
        }).done(function (response) {
            if (response.result === 'IoTBox connected'){
                self._updateIOT(url, 'success', response.result);
            } else {
                self._updateIOT(url, 'error', response.result);
            }
        }).fail(function (){
            self._updateIOT(url, 'error', _t('Connection failed'));
        });
    },

    _onButtonClick: function (e) {
        this.$el.attr('disabled', true);
        this._findIOTs();
    },
});

widget_registry.add('iot_detect_button', IotDetectButton);

var IoTCoreMixin = {
    parseURL: new URL(window.location.href),
    _url: function (iot_ip){
        var port = '';
        if(this.parseURL.protocol == 'http:'){
            port = ':8069';
        }
        return this.parseURL.protocol + "//" + this.record.data.ip + port;
    },

    _callIotDevice: function (url, data, iot_ip){
        if (data) {
            return $.ajax({
                type: 'POST',
                url: url,
                dataType: 'json',
                contentType: "application/json; charset=utf-8",
                data: JSON.stringify(data),
            }).fail(this._onFail.bind(this, iot_ip));
        } else {
            return $.get(url).fail(this._onFail.bind(this, iot_ip));
        }
    },

    _onFail: function (iot_ip, jqXHR, textStatus){
        switch (textStatus){
            case "error":
                if (this.parseURL.protocol === 'https:'){
                    this._doWarnCertificate(iot_ip);
                } else {
                    this._doWarnError();
                }
                break;
            case "timeout":
                this._doWarnTimeout();
                break;
            default:
                this._doWarnError();
        }
    },
    _doWarnError: function (){
        var $content = $('<p/>').text(_t('Please check if the device is still connected.'));
        var dialog = new Dialog(this, {
            title: _t('Connection to device failed'),
            $content: $content,
        });
        dialog.open();
    },
    _doWarnTimeout: function (){
        var $content = $('<p/>').text(_t('Please check if the device is still connected.'));
        var dialog = new Dialog(this, {
            title: _t('The device is not responding'),
            $content: $content,
        });
        dialog.open();
    },
    _doWarnCertificate: function (iot_ip){
        var $ol = $('<ol/>')
            .append(_.str.sprintf('<li><a href="%s" target="_blank"><i class="fa fa-external-link"/> ' + _t('Click here to open your IoT Homepage') + '</a></li>', iot_ip))
            .append('<li>' + _t('Click on Advanced/Show Details/Details/More information') + '</li>')
            .append('<li>' + _t('Click on Proceed to .../Add Exception/Visit this website/Go on to the webpage') + '</li>')
            .append('<li>' + _t('Firefox only : Click on Confirm Security Exception') + '</li>')
            .append('<li>' + _t('Close this window and try again') + '</li>');

        var $content = $('<div/>')
            .append('<p>' + _t("Please accept the certificate of your IoT Box (procedure depends on your browser) :") + '</p>')
            .append($ol);

        var dialog = new Dialog(this, {
            title: _t('Connection to device failed'),
            $content: $content,
            buttons: [
                {
                    text: _t("Close"),
                    classes: "btn-secondary o_form_button_cancel",
                    close: true,
                }
            ],
        });

        dialog.open();
    },
};

var IotTakeMeasureButton = Widget.extend(IoTCoreMixin, {
    tagName: 'button',
    className: 'btn btn-primary',
    events: {
        'click': '_onButtonClick',
    },

    /**
     * @override
     */
    init: function (parent, record, node) {
        this.record = record;
        this.options = py_eval(node.attrs.options);
        this._super.apply(this, arguments);
    },
    /**
     * @override
     */
    start: function () {
        this._super.apply(this, arguments);
        this.$el.text(_t('Take Measure'));
        this.$el.attr('barcode_trigger', 'measure');
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _onButtonClick: function () {
        var self = this;
        var identifier = this.record.data[this.options.identifier_field];
        var composite_url = this._url() + "/hw_drivers/driverdetails/" + identifier;
        var measure_field = this.options.measure_field;

        return this._callIotDevice(composite_url, null, this._url()).done(function (measure) {
            var changes = {};
            changes[measure_field] = parseFloat(measure);
            self.trigger_up('field_changed', {
                dataPointID: self.record.id,
                changes: changes,
            });
        });
    },
});

widget_registry.add('iot_take_measure_button', IotTakeMeasureButton);

return {
    IotDetectButton: IotDetectButton,
    IotTakeMeasureButton: IotTakeMeasureButton,
    IoTCoreMixin: IoTCoreMixin,
};
});


