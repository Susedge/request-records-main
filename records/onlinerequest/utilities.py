def get_if_exists(model, **kwargs):
    try:
        obj = model.objects.get(**kwargs)
    except Exception as e:
        obj = None

    return obj