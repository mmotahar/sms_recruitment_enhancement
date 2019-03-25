odoo.define('quality_mrp_iot.pedal_form', function(require) {
"use strict";

var FormView = require('web.FormView');
var FormController = require('web.FormController');
var FormRenderer = require('web.FormRenderer');
var view_registry = require('web.view_registry');

var PedalRenderer = FormRenderer.extend({
    events: _.extend({}, FormRenderer.prototype.events, {
        'click .o_pedal_status_button': '_onPedalStatusButtonClicked',
    }),

    init: function () {
        this._super.apply(this, arguments);
        this.pedal_connect = false;
        this.show_pedal_button = false;
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    showPedalStatusButton: function (connected) {
        this.pedal_connect = connected;
        this.show_pedal_button = true;
        return this._updatePedalStatusButton(); // maybe only update the button
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     * @private
     */
    _render: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            self._updatePedalStatusButton();
        });
    },

    _updatePedalStatusButton: function () {
        this.$('.o_pedal_status_button').remove();
        var self = this;
        if (this.show_pedal_button) {
            var button = $('<button>', {
                class: 'btn o_pedal_status_button ' + (self.pedal_connect ? ' btn-primary o_active ' : ' btn-warning'),
                disabled: self.pedal_connect,
            });
            button.html('<i class="fa fa-clipboard"></i>');
            this.$('.o_workorder_actions').append(button);
        }
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    _onPedalStatusButtonClicked: function (ev) {
        ev.preventDefault();
        this.trigger_up('pedal_status_button_clicked');
    },
});


var PedalController = FormController.extend({
    custom_events: _.extend({}, FormController.prototype.custom_events, {
        'pedal_status_button_clicked': '_onTakeOwnership',
    }),

    /**
    * When it starts, it needs to check if the tab owns or can take ownership of the devices
    * already.  If not, an indicator button will show in orange and you can click on it
    * in order to still take ownership.
    **/
    start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            var state = self.model.get(self.handle);
            self.triggers = $.parseJSON(state.data.boxes); //or JSON.parse?
            var data = self.triggers;
            // Check Tab id
            self.tabID = sessionStorage.tabID ? sessionStorage.tabID : sessionStorage.tabID = Math.random().toString();

            // Call IoT Boxes
            var promises = [];
            console.log(data);
            var protocol = new URL(window.location.href).protocol;
            var port = protocol === 'http' ? ':8069' : '';
            _.each(self.triggers, function (trigger, triggerName) {
                trigger.url = protocol + '//' + triggerName + port;
            });
            for (var key in data) {
                var url = data[key].url + '/hw_drivers/owner/check';
                var devices = [];
                for (var device in data[key]) {
                    devices.push(data[key][device][0]);
                }
                devices = _.uniq(devices);
                var json_data = {'devices': devices, 'tab': self.tabID};
                console.log(json_data);
                promises.push($.ajax({type: 'POST',
                    url: url,
                    dataType: 'json',
                    beforeSend: function(xhr){xhr.setRequestHeader('Content-Type', 'application/json');},
                    data: JSON.stringify(json_data),
                    }));
            }
            if (promises.length) {
                $.when.apply($, promises).then(function () {
                    self.can_check = true;
                    for (var arg in arguments) { //TODO: need to see difference between one or two returns
                        if (arguments[arg].result === 'no') {
                            self.can_check = false;
                            break;
                        }
                    }
                    if (self.can_check) {
                        self.take_ownerships();
                    }
                    else {
                        self.renderer.showPedalStatusButton(false);
                    }
                });
            }
        });
    },

    destroy: function() {
        //Stop pinging
        var self = this;
        clearInterval(self.mytimer);
    },


    /*
    * This function tells the IoT Box that this browser tab will take control
    * over the devices of this workcenter.  When done, a timer is started to
    * check if a pedal was pressed every half second, which will handle further actions.
    */
    take_ownerships: function() {
        var self = this;
        this.renderer.showPedalStatusButton(true);
        var data = this.triggers;
        for (var key in data) {
            var url = data[key].url + '/hw_drivers/owner/take';
            var devices = [];
            for (var device in data[key]) {
                devices.push(data[key][device][0]);
            }
            devices = _.uniq(devices);
            var json_data = {'devices': devices, 'tab': self.tabID};
            console.log(json_data);
            $.ajax({type: 'POST',
                    url: url,
                    dataType: 'json',
                    beforeSend: function(xhr) {xhr.setRequestHeader('Content-Type', 'application/json');},
                    data: JSON.stringify(json_data),
            }).then(function(result) {
                self.mytimer = setInterval(self.ping.bind(self), 500);
            });
        }
    },

    /**
    * This function is called every x time to check if a pedal was pressed.
    * If so, it will check all the triggers connected to this workcenter
    * in order to see if we need to execute a click on a button, similar
    * to the barcode_trigger for the barcodes.
    **/
    ping: function() {
        var self = this;
        var data = this.triggers;
        for (var box in data) {
            var url = data[box].url + '/hw_drivers/owner/ping';
            var devices = [];
            for (var device in data[box]) {
                devices.push(data[box][device][0]);
            }
            devices = _.uniq(devices);
            var json_data = {'tab': sessionStorage.tabID, 'devices': devices};
            $.ajax({type: 'POST',
                    url: url,
                    dataType: 'json',
                    beforeSend: function(xhr) {xhr.setRequestHeader('Content-Type', 'application/json');},
                    data: JSON.stringify(json_data),
            }).then(function (result) {
                for (var key in result['result']) {
                    // Filter all devices connected to this workcenter to see which one corresponds
                    for (var dev in data[box]) {
                        var dev_list = data[box][dev];
                        if (dev_list[0] === key) {
                            if (result['result'][key] === 'STOP') {
                                self.renderer.showPedalStatusButton(false);
                                clearInterval(self.mytimer);
                            }
                            if (!dev_list[1] || result['result'][key].toUpperCase() === dev_list[1].toUpperCase()) {
                                $("button[barcode_trigger='" + dev_list[2] + "']:visible").click();
                            }
                        }
                    }
                }
            });
        }
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {OdooEvent} ev
     */
    _onTakeOwnership: function (ev) {
        ev.stopPropagation();
        this.take_ownerships();
    },
});

var PedalForm = FormView.extend({
    config: _.extend({}, FormView.prototype.config, {
        Controller: PedalController,
        Renderer: PedalRenderer,
    }),
});

view_registry.add('pedal_form', PedalForm);
});