"""
All views that visualise a model object (banana.models)
"""
from django.db.models import Count, Max, Avg
from django.views.generic import DetailView
from django.views.generic import ListView
from django.shortcuts import get_object_or_404
import banana.image
from banana.models import (Image, Dataset, Extractedsource,
                            AugmentedRunningcatalog,
                          Newsource, Assocxtrsource, Monitor)
from banana.views.mixins import (HybridTemplateMixin,
                                DatasetMixin, SortListMixin,FluxViewMixin)
from collections import OrderedDict


class ImageDetail(FluxViewMixin, SortListMixin, DatasetMixin,
                      HybridTemplateMixin, ListView):
    model = Image
    paginate_by = 20
    template_name = "banana/image_detail.html"

    def get_size(self):
        image_size = 4  # in inches
        return image_size

    def get_queryset(self):
        qs = super(ImageDetail, self).get_queryset()
        self.object = get_object_or_404(qs, id=self.kwargs['pk'])
        return self.object.extractedsources.all().order_by(self.get_order())

    def get_context_data(self, **kwargs):
        context = super(ImageDetail, self).get_context_data(**kwargs)
        context['image_size'] = self.get_size()
        context['pixels'] = banana.image.extracted_sources_pixels(self.object,
                                                               self.get_size())
        context['object'] = self.object
        return context


class BigImageDetail(DatasetMixin, DetailView):
    template_name = "banana/bigimage_detail.html"
    model = Image
    image_size = 8

    def get_context_data(self, **kwargs):
        context = super(BigImageDetail, self).get_context_data(**kwargs)
        context['image_size'] = self.image_size
        context['sources'] = banana.image.extracted_sources_pixels(self.object,
                                                               self.image_size)
        return context


class DatasetDetail(DetailView):
    model = Dataset

    def get_context_data(self, **kwargs):
        context = super(DatasetDetail, self).get_context_data(**kwargs)

        # annotated images
        related = ['band']
        images = Image.objects.using(self.request.SELECTED_DATABASE). \
            filter(dataset=self.object). \
            prefetch_related(*related). \
            annotate(num_extractedsources=Count('extractedsources')). \
            order_by('taustart_ts')
        images_per_band = {}
        for image in images:
            label = str(image.band)
            images_per_band.setdefault(label, [])
            images_per_band[label].append(image.num_extractedsources)
        images_per_band = OrderedDict(sorted(images_per_band.iteritems(),
                                             key=lambda x: x[0]))
        context['dataset'] = self.object
        context['num_extractedsources'] = Extractedsource.objects.\
            using(self.request.SELECTED_DATABASE).\
            filter(image__in=images.all()).count()
        context['images'] = images
        context['images_per_band'] = images_per_band
        return context


class ExtractedSourceDetail(DetailView):
    model = Extractedsource

    def get_context_data(self, **kwargs):
        context = super(ExtractedSourceDetail, self).get_context_data(**kwargs)
        context['extractedsource'] = self.object
        return context


class MonitorDetail(DetailView):
    model = Monitor



class NewsourceDetail(SortListMixin, DatasetMixin,
                      HybridTemplateMixin, ListView):
    model = Newsource
    paginate_by = 100
    default_order = 'image__taustart_ts'
    template_name = "banana/newsource_detail.html"

    def get_queryset(self):
        qs = super(NewsourceDetail, self).get_queryset()
        self.object = get_object_or_404(qs, id=self.kwargs['pk'])
        return self.object.runcat.extractedsources.order_by(self.get_order())

    def get_context_data(self, **kwargs):
        context = super(NewsourceDetail, self).get_context_data(**kwargs)
        context['object'] = self.object
        return context


class RunningcatalogDetail(FluxViewMixin, SortListMixin, DatasetMixin,
                           HybridTemplateMixin, ListView):
    model = AugmentedRunningcatalog
    paginate_by = 100
    default_order = 'xtrsrc__image__taustart_ts'
    template_name = "banana/runningcatalog_detail.html"

    def get_queryset(self):
        qs = super(RunningcatalogDetail, self).get_queryset()\
            .select_related('xtrsrc', 'assocxtrsources')
        self.object = get_object_or_404(qs, id=self.kwargs['pk'])
        assoc_related = ['xtrsrc', 'xtrsrc__image', 'xtrsrc__image__band']
        return Assocxtrsource.objects.using(qs.db)\
            .filter(runcat=self.object.id)\
            .select_related(*assoc_related)\
            .order_by(self.get_order())

    def get_context_data(self, **kwargs):
        context = super(RunningcatalogDetail, self).get_context_data(**kwargs)
        context['object'] = self.object
        return context
