"""Pure lifetime policy, shared with the generated Kaggle notebook."""
def stop_reason(started,last_activity,active_requests,now,idle_minutes=15,max_minutes=120):
    if now-started>=max_minutes*60:return 'limite de sesion'
    if active_requests==0 and now-last_activity>=idle_minutes*60:return 'inactividad'
    return None
