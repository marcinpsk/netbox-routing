from utilities.choices import ChoiceSet


class OSPFNetworkTypeChoices(ChoiceSet):
    BROADCAST = 'broadcast'
    NON_BROADCAST = 'non-broadcast'
    POINT_TO_POINT = 'point-to-point'
    POINT_TO_MULTIPOINT = 'point-to-multipoint'

    CHOICES = [
        (BROADCAST, 'Broadcast'),
        (NON_BROADCAST, 'Non-Broadcast'),
        (POINT_TO_POINT, 'Point-to-Point'),
        (POINT_TO_MULTIPOINT, 'Point-to-Multipoint'),
    ]


class OSPFAreaTypeChoices(ChoiceSet):
    STANDARD = 'standard'
    BACKBONE = 'backbone'
    STUB = 'stub'
    TSA = 'tsa'
    NSSA = 'nssa'
    TNSSA = 'tnssa'

    CHOICES = [
        (STANDARD, 'Standard Area'),
        (BACKBONE, 'Backbone Area'),
        (STUB, 'Stub Area'),
        (TSA, 'Totally Stubby Area'),
        (NSSA, 'Not-So-Stubby Area'),
        (TNSSA, 'Totally Not-So-Stubby Area'),
    ]
