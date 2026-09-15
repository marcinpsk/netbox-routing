from django.db import migrations

FORWARD_SQL = """
CREATE FUNCTION netbox_routing_check_staticroute_device_triple()
RETURNS trigger AS $$
BEGIN
    PERFORM route.id
    FROM netbox_routing_staticroute AS route
    WHERE route.id = NEW.staticroute_id
    FOR SHARE;

    PERFORM device.id
    FROM dcim_device AS device
    WHERE device.id = NEW.device_id
    FOR UPDATE;

    IF EXISTS (
        SELECT 1
        FROM netbox_routing_staticroute_devices AS existing_link
        JOIN netbox_routing_staticroute AS existing_route
          ON existing_route.id = existing_link.staticroute_id
        JOIN netbox_routing_staticroute AS candidate_route
          ON candidate_route.id = NEW.staticroute_id
        WHERE existing_link.device_id = NEW.device_id
          AND existing_link.id IS DISTINCT FROM NEW.id
          AND existing_link.staticroute_id <> NEW.staticroute_id
          AND existing_route.vrf_id IS NOT DISTINCT FROM candidate_route.vrf_id
          AND existing_route.prefix IS NOT DISTINCT FROM candidate_route.prefix
          AND existing_route.next_hop IS NOT DISTINCT FROM candidate_route.next_hop
    ) THEN
        RAISE unique_violation USING
            MESSAGE = 'A device cannot hold the same static route twice.',
            CONSTRAINT = 'netbox_routing_staticroute_device_triple_unique';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER netbox_routing_staticroute_devices_unique_triple
BEFORE INSERT OR UPDATE ON netbox_routing_staticroute_devices
FOR EACH ROW
EXECUTE FUNCTION netbox_routing_check_staticroute_device_triple();

CREATE FUNCTION netbox_routing_check_staticroute_triple_update()
RETURNS trigger AS $$
BEGIN
    IF NEW.vrf_id IS NOT DISTINCT FROM OLD.vrf_id
       AND NEW.prefix IS NOT DISTINCT FROM OLD.prefix
       AND NEW.next_hop IS NOT DISTINCT FROM OLD.next_hop THEN
        RETURN NEW;
    END IF;

    PERFORM device.id
    FROM dcim_device AS device
    JOIN netbox_routing_staticroute_devices AS candidate_link
      ON candidate_link.device_id = device.id
    WHERE candidate_link.staticroute_id = NEW.id
    ORDER BY device.id
    FOR UPDATE OF device;

    IF EXISTS (
        SELECT 1
        FROM netbox_routing_staticroute_devices AS candidate_link
        JOIN netbox_routing_staticroute_devices AS existing_link
          ON existing_link.device_id = candidate_link.device_id
        JOIN netbox_routing_staticroute AS existing_route
          ON existing_route.id = existing_link.staticroute_id
        WHERE candidate_link.staticroute_id = NEW.id
          AND existing_link.staticroute_id <> NEW.id
          AND existing_route.vrf_id IS NOT DISTINCT FROM NEW.vrf_id
          AND existing_route.prefix IS NOT DISTINCT FROM NEW.prefix
          AND existing_route.next_hop IS NOT DISTINCT FROM NEW.next_hop
    ) THEN
        RAISE unique_violation USING
            MESSAGE = 'A device cannot hold the same static route twice.',
            CONSTRAINT = 'netbox_routing_staticroute_device_triple_unique';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER netbox_routing_staticroute_unique_triple_update
BEFORE UPDATE OF vrf_id, prefix, next_hop ON netbox_routing_staticroute
FOR EACH ROW
EXECUTE FUNCTION netbox_routing_check_staticroute_triple_update();
"""

REVERSE_SQL = """
DROP TRIGGER netbox_routing_staticroute_unique_triple_update
ON netbox_routing_staticroute;
DROP FUNCTION netbox_routing_check_staticroute_triple_update();

DROP TRIGGER netbox_routing_staticroute_devices_unique_triple
ON netbox_routing_staticroute_devices;
DROP FUNCTION netbox_routing_check_staticroute_device_triple();
"""


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_routing', '0038_alter_community_community'),
    ]

    operations = [
        migrations.RunSQL(FORWARD_SQL, reverse_sql=REVERSE_SQL),
    ]
