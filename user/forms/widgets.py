from django.forms import RadioSelect


class ColorRadioSelect(RadioSelect):
    template_name = 'user/widgets/color_radio/radio.html'
    option_template_name = 'user/widgets/color_radio/radio_option.html'
