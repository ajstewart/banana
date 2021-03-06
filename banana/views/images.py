"""
All views that generate images
"""
from django.http import HttpResponse
import banana.image
from StringIO import StringIO
from banana.rms import rms_histogram
from banana.models import Extractedsource, Image, Dataset
from django.views.generic import DetailView


class ImagePlot(DetailView):
    model = Image

    def get_context_data(self, **kwargs):
        context = super(ImagePlot, self).get_context_data(**kwargs)
        context['sources'] = self.object.extractedsources.all()
        try:
            context['size'] = int(self.request.GET.get('size', 5))
        except ValueError:
             context['size'] = 5
        context['hdu'] = banana.image.reconstruct_fits(self.object)
        return context

    def render_to_response(self, context, **kwargs):
        response = HttpResponse(content_type="image/png")
        if context['hdu']:
            canvas = banana.image.image_plot(context['hdu'], context['size'],
                                             context['sources'])
            canvas.print_figure(response, format='png', bbox_inches='tight',
                                pad_inches=0, dpi=100)
        return response


class ExtractedSourcePlot(DetailView):
    model = Extractedsource

    def get_context_data(self, **kwargs):
        context = super(ExtractedSourcePlot, self).get_context_data(**kwargs)
        context['size'] = int(self.request.GET.get('size', 1))
        context['hdu'] = banana.image.reconstruct_fits(self.object.image)
        return context

    def render_to_response(self, context, **kwargs):
        response = HttpResponse(content_type="image/png")
        if context['hdu']:
            canvas = banana.image.extractedsource(context['hdu'], self.object,
                                                  context['size'])
            canvas.print_figure(response, format='png', bbox_inches='tight',
                                pad_inches=0, dpi=100)
        return response


class RawImage(DetailView):
    model = Image

    def render_to_response(self, context, **kwargs):
        s = StringIO()
        handler = banana.image.reconstruct_fits(self.object)
        handler.writeto(s)
        response = HttpResponse(s.getvalue(), content_type="application/octet-stream")
        response['Content-Disposition'] = 'attachment; filename="banana.fits"'
        return response


class DatasetRmsImage(DetailView):
    model = Dataset

    def get_context_data(self, **kwargs):
        context = super(DatasetRmsImage, self).get_context_data(**kwargs)
        context['frequency'] = float(self.request.GET.get('frequency', False))
        return context

    def render_to_response(self, context, **kwargs):
        query = self.object.images.values_list('rms_qc', flat=True)
        if context['frequency']:
            display_freq = '{:.3f} MHz'.format(float(context['frequency']) / 10**6)
            rms_values = query.filter(band__freq_central=context['frequency'])
        else:
            display_freq = 'all'
            rms_values = query.all()

        est_sigma = float(self.object.configs.get(section='persistence',
                                                  key='rms_est_sigma').value)

        canvas = rms_histogram(rms_values, est_sigma, display_freq)
        response = HttpResponse(content_type="image/png")
        canvas.print_figure(response, format='png')
        return response