#!/usr/bin/env python3
import click
import sys
import json
import yaml
import datetime
from datetime import timezone
from pathlib import Path
from megaid import MEGAID

# Initialize MEGAID instance with environment variables
try:
    megaid = MEGAID()  # Will load from environment or generate new keys
except Exception as e:
    click.echo(click.style("Error initializing MEGAID:", fg="red"))
    click.echo(click.style(str(e), fg="red"))
    sys.exit(1)

def validate_timestamp(ctx, param, value):
    """Validate and parse timestamp format."""
    if not value:
        return None
    try:
        dt = datetime.datetime.strptime(value, "%Y-%m-%d:%H:%M")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        raise click.BadParameter('Timestamp must be in format YYYY-MM-DD:HH:MM')

@click.group()
def cli():
    """MEGAID CLI - Generate and manage compound identifiers."""
    pass

@cli.command()
@click.argument(
    'yaml_file',
    type=click.Path(exists=True, dir_okay=False),
    required=False
)
def create_utc(yaml_file):
    """Create a new ID using current UTC time and optional YAML data."""
    try:
        now = datetime.datetime.now(timezone.utc)
        
        # Default data
        immutable_data = {"created_at": now.isoformat()}
        mutable_data = {"last_updated": now.isoformat()}
        
        # If YAML file provided, load and merge data
        if yaml_file:
            try:
                with open(yaml_file, 'r') as f:
                    yaml_data = yaml.safe_load(f)
                
                if not isinstance(yaml_data, dict):
                    raise click.ClickException("YAML file must contain a dictionary")
                
                # Update with YAML data if provided, keeping defaults if not
                if 'immutable_data' in yaml_data:
                    immutable_data.update(yaml_data['immutable_data'])
                if 'mutable_data' in yaml_data:
                    mutable_data.update(yaml_data['mutable_data'])
                    
            except yaml.YAMLError as e:
                raise click.ClickException(f"Error parsing YAML file: {str(e)}")
        
        compound_id = megaid.create(
            immutable_data=immutable_data,
            mutable_data=mutable_data
        )
        click.echo(f"New UTC-based ID: {compound_id}")
    except Exception as e:
        raise click.ClickException(str(e))

@cli.command()
@click.option(
    '--timestamp',
    required=True,
    callback=validate_timestamp,
    help='Timestamp in format YYYY-MM-DD:HH:MM'
)
def create_custom(timestamp):
    """Create a new ID using a custom timestamp."""
    try:
        compound_id = megaid.create(
            immutable_data={"created_at": timestamp.isoformat()},
            mutable_data={
                "last_updated": datetime.datetime.now(timezone.utc).isoformat()
            }
        )
        click.echo(f"New custom time-based ID: {compound_id}")
    except Exception as e:
        raise click.ClickException(str(e))

@cli.command()
@click.argument('id_to_decode')
def decode(id_to_decode):
    """Decode and display metadata from a MEGAID.
    
    Accepts either a full compound ID or just a snowflake ID.
    Format: snowflake:immutable:mutable or just snowflake
    """
    try:
        if ':' not in id_to_decode:
            # This is just a snowflake ID
            try:
                snowflake_int = int(id_to_decode)
                click.echo("\nSnowflake ID Analysis:")
                click.echo("--------------------")
                click.echo(click.style("Snowflake ID:", fg="green"))
                click.echo(click.style(str(snowflake_int), fg="white"))
                # Extract timestamp from snowflake using MEGAID's decode method
                timestamp_ms, random_bits = megaid._decode_megaid(snowflake_int)
                timestamp = datetime.datetime.fromtimestamp(
                    timestamp_ms / 1000,
                    tz=timezone.utc
                )
                
                click.echo(click.style("\nTimestamp:", fg="blue"))
                click.echo(click.style(timestamp.isoformat(), fg="white"))
                
                click.echo(click.style("\nRandom Bits:", fg="yellow"))
                click.echo(click.style(str(random_bits), fg="white"))
                return
            except ValueError:
                raise click.ClickException(
                    "Invalid snowflake ID format. Must be a number."
                )
        
        # This is a full compound ID
        try:
            data = megaid.read(id_to_decode)
            
            # Check if we got valid data back
            if not data:
                raise click.ClickException("Failed to decode MEGAID")
            
            # Display the data
            click.echo("\nDecoded Compound ID Data:")
            click.echo("----------------------")
            click.echo(click.style("\nMEGAID:", fg="cyan"))
            click.echo(click.style(str(data['megaid']), fg="white"))
            
            # Convert timestamps to readable format
            created_date = datetime.datetime.fromtimestamp(
                data['date_created'] / 1000,
                tz=timezone.utc
            )
            updated_date = datetime.datetime.fromtimestamp(
                data['date_updated'] / 1000,
                tz=timezone.utc
            )
            
            click.echo(click.style("\nCreated At:", fg="blue"))
            click.echo(click.style(created_date.isoformat(), fg="white"))
            click.echo(click.style("\nLast Updated:", fg="yellow"))
            click.echo(click.style(updated_date.isoformat(), fg="white"))
            
            click.echo(click.style("\nRandom Bits:", fg="magenta"))
            click.echo(click.style(str(data['random_bits']), fg="white"))
            
            click.echo(click.style("\nImmutable Data:", fg="green"))
            immutable_json = json.dumps(data['immutable_data'], indent=2)
            click.echo(click.style(immutable_json, fg="white"))
            click.echo(click.style("\nMutable Data:", fg="yellow"))
            mutable_json = json.dumps(data['mutable_data'], indent=2)
            click.echo(click.style(mutable_json, fg="white"))
        except Exception as e:
            raise click.ClickException(f"Error decoding compound ID: {str(e)}")
            
    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Error: {str(e)}")

if __name__ == '__main__':
    cli()