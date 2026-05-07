def make_job(
    source,
    dest,
    timer_hours=24,
    paused=False,
    last_backup=None,
    incomplete=False,
):
    """
    Creates a job dictionary compatible with current system.
    """
    return {
        "source": source,
        "dest": dest,
        "timer_hours": timer_hours,
        "paused": paused,
        "last_backup": last_backup,
        "incomplete": incomplete,
    }


def validate_job(job):
    """
    Validates minimal job structure.
    """
    required_keys = ["source", "dest", "timer_hours"]

    for key in required_keys:
        if key not in job:
            return False

    return True