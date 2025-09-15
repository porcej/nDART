/**
 * [Selectize](https://selectize.github.io/selectize.js/) enhances the HTML
 * `<select>` element with a beautifully styled input control, that features
 * tags, text input, auto-complete and much more.
 *
 * @name Selectize
 * @summary Use the Selectize library with Editor for complex select input options.
 * @requires [Selectize](https://selectize.github.io/selectize.js/)
 * @depcss //cdnjs.cloudflare.com/ajax/libs/selectize.js/0.9.0/css/selectize.css
 * @depjs //cdnjs.cloudflare.com/ajax/libs/selectize.js/0.9.0/js/standalone/selectize.js
 * 
 * @opt `e-type object` **`options`**: Options that are given to the selectize
 *     `addOption` method.
 * @opt `e-type object` **`opts`**: Selectize initialisation options object.
 *     Please refer to the Selectize documentation for the full range
 *     of options available.
 * @opt `e-type object` **`attr`**: Attributes that are applied to the
 *     `-tag select` element before selectize is initialised
 *
 * @method **`inst`**: Get the selectize instance
 * @method **`update`**: Clear existing options and add new items
 *
 * @scss editor.selectize.scss
 *
 * @example
 *   new $.fn.dataTable.Editor( {
 *   "ajax": "php/tableFormatting.php",
 *   "table": "#example",
 *   "fields": [ {
 *           "label": "Item:",
 *           "name": "item"
 *       }, {
 *           "label": "Priority:",
 *           "name": "priority",
 *           "type": "selectize",
 *           "options": [
 *               { "label": "1 (highest)", "value": "1" },
 *               { "label": "2",           "value": "2" },
 *               { "label": "3",           "value": "3" },
 *               { "label": "4",           "value": "4" },
 *               { "label": "5 (lowest)",  "value": "5" }
 *           ]
 *       }, {
 *           "label": "Status:",
 *           "name": "status",
 *           "type": "radio",
 *           "default": "Done",
 *           "options": [
 *               { "label": "To do", "value": "To do" },
 *               { "label": "Done", "value": "Done" }
 *           ]
 *       }
 *   ]
 * } );
 */

(function( factory ){
    if ( typeof define === 'function' && define.amd ) {
        // AMD
        define( ['jquery', 'datatables', 'datatables-editor'], factory );
    }
    else if ( typeof exports === 'object' ) {
        // Node / CommonJS
        module.exports = function ($, dt) {
            if ( ! $ ) { $ = require('jquery'); }
            factory( $, dt || $.fn.dataTable || require('datatables') );
        };
    }
    else if ( jQuery ) {
        // Browser standard
        factory( jQuery, jQuery.fn.dataTable );
    }
}(function( $, DataTable ) {
'use strict';


if ( ! DataTable.ext.editorFields ) {
    DataTable.ext.editorFields = {};
}

var _fieldTypes = DataTable.Editor ?
    DataTable.Editor.fieldTypes :
    DataTable.ext.editorFields;


_fieldTypes.selectize = {
    _addOptions: function ( conf, options ) {
        var selectize = conf._selectize;

        if (!selectize) {
            console.error('Selectize instance not available for adding options');
            return;
        }

        // Clear existing options
        if (typeof selectize.clearOptions === 'function') {
            selectize.clearOptions();
        } else if (typeof selectize.clear === 'function') {
            selectize.clear();
        }
        
        // Add new options
        if (typeof selectize.addOption === 'function') {
            selectize.addOption( options );
        }
        
        // Refresh options
        if (typeof selectize.refreshOptions === 'function') {
            selectize.refreshOptions(false);
        }
    },
 
    create: function ( conf ) {
        var container = $('<div/>');
        conf._input = $('<select/>')
                .attr( $.extend( {
                    id: conf.id
                }, conf.attr || {} ) )
            .appendTo( container );
 
        // Check if selectize is available
        if (typeof $.fn.selectize !== 'function') {
            console.error('Selectize plugin not loaded. Please ensure selectize.js is loaded before this plugin.');
            console.log('jQuery version:', $.fn.jquery);
            console.log('Available jQuery plugins:', Object.keys($.fn).filter(key => key.includes('select')));
            return container[0];
        }
        
        try {
            conf._input.selectize( $.extend( {
                valueField: 'value',
                labelField: 'label',
                searchField: 'label',
                dropdownParent: 'body'
            }, conf.opts ) );

            // Get the selectize instance - try both old and new ways
            conf._selectize = conf._input[0].selectize || conf._input.data('selectize');
            
            if (!conf._selectize) {
                console.error('Could not access selectize instance');
                return container[0];
            }
        } catch (error) {
            console.error('Error initializing selectize:', error);
            return container[0];
        }

        if ( conf.options || conf.ipOpts ) {
            _fieldTypes.selectize._addOptions( conf, conf.options || conf.ipOpts );
        }

        // Make sure the select list is closed when the form is submitted
        this.on( 'preSubmit', function () {
            if (conf._selectize && typeof conf._selectize.close === 'function') {
                conf._selectize.close();
            }
        } );
 
        return container[0];
    },
 
    get: function ( conf ) {
        if (!conf._selectize) {
            console.error('Selectize instance not available for get');
            return '';
        }
        return conf._selectize.getValue();
    },
 
    set: function ( conf, val ) {
        if (!conf._selectize) {
            console.error('Selectize instance not available for set');
            return;
        }
        return conf._selectize.setValue( val );
    },
 
    enable: function ( conf ) {
        if (!conf._selectize) {
            console.error('Selectize instance not available for enable');
            return;
        }
        conf._selectize.enable();
        $(conf._input).removeClass( 'disabled' );
    },
 
    disable: function ( conf ) {
        if (!conf._selectize) {
            console.error('Selectize instance not available for disable');
            return;
        }
        conf._selectize.disable();
        $(conf._input).addClass( 'disabled' );
    },
 
    // Non-standard Editor methods - custom to this plug-in
    inst: function ( conf ) {
        return conf._selectize;
    },

    update: function ( conf, options ) {
        _fieldTypes.selectize._addOptions( conf, options );
    },

    canReturnSubmit: function () {
		return true;
    }
};


}));
