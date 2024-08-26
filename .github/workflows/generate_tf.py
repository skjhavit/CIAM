import yaml
import os
import sys
import traceback
import json

def format_terraform_value(value):
    if isinstance(value, list):
        return json.dumps(value)
    elif isinstance(value, str):
        return f'"{value}"'
    else:
        return value

try:
    os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    # Find the YAML file (excluding template.yml)
    yaml_files = [f for f in os.listdir('.') if f.endswith('.yml') and f != 'template.yml']
    if not yaml_files:
        raise FileNotFoundError("No YAML configuration file found")

    yaml_file = yaml_files[0]

    # Load the YAML file
    with open(yaml_file, 'r') as file:
        config = yaml.safe_load(file)

    # Get Okta API token from environment variable
    okta_api_token = os.getenv('OKTA_API_TOKEN')

    if not okta_api_token:
        raise ValueError("Okta API token is not set")

    # Initialize the Terraform configuration with the required provider settings
    tf_config = f"""
    terraform {{
      required_providers {{
        okta = {{
          source  = "okta/okta"
          version = "3.41.0"
        }}
      }}
    }}

    provider "okta" {{
      org_name   = "dev-176298"
      base_url   = "okta.com"
      api_token  = "{okta_api_token}"
    }}
    """

    # Determine the scenario and generate the corresponding Terraform resources
    config = config['scenarios'][0]
    scenario_name = config['name']
    
    if scenario_name == 'create_application_and_group':
        # Add the Okta application resource
        tf_config += f"""
        resource "okta_app_oauth" "dxp_app" {{
          label             = {format_terraform_value(config['label'])}
          type              = {format_terraform_value(config['type'])}
          grant_types       = ["implicit", "authorization_code"]
          response_types    = {format_terraform_value(config['response_types'])}
          redirect_uris     = {format_terraform_value(config['redirect_uris'])}
          post_logout_redirect_uris = {format_terraform_value(config.get('post_logout_redirect_uris', []))}
          client_uri        = {format_terraform_value(config.get('client_uri', ''))}
          tos_uri           = {format_terraform_value(config.get('tos_uri', ''))}
          policy_uri        = {format_terraform_value(config.get('policy_uri', ''))}
        }}
        """

        # Dynamically generate group resources based on the groups provided in the YAML file
        for index, group_name in enumerate(config['groups']):
            tf_config += f"""
            resource "okta_group" "group_{index}" {{
              name        = {format_terraform_value(group_name)}
              description = "Group {index + 1} for {config['app_name']} app"
            }}
            """

        # Dynamically assign the groups to the application
        tf_config += f"""
        resource "okta_app_group_assignments" "dxp_app_assignments" {{
          app_id = okta_app_oauth.dxp_app.id
        """
        for index in range(len(config['groups'])):
            tf_config += f"""
          group {{
            id = okta_group.group_{index}.id
          }}"""
        tf_config += """
        }
        """

        # Output the client secret for the application
        tf_config += f"""
        output "dxp_app_client_secret" {{
          value       = okta_app_oauth.dxp_app.client_secret
          sensitive   = true
          description = "The client secret for the {config['app_name']} App"
        }}
        """

    elif scenario_name == 'create_group_for_existing_application':
        # Dynamically generate group resources for an existing application
        for index, group_name in enumerate(config['groups']):
            tf_config += f"""
            resource "okta_group" "group_{index}" {{
              name        = {format_terraform_value(group_name)}
              description = "Group {index + 1} for existing application {config['application_id']}"
            }}
            """

        # Dynamically assign the new groups to the existing application
        tf_config += f"""
        resource "okta_app_group_assignments" "new_dxp_app_assignments" {{
          app_id = "{config['application_id']}"
        """
        for index in range(len(config['groups'])):
            tf_config += f"""
          group {{
            id = okta_group.group_{index}.id
          }}"""
        tf_config += """
        }
        """

    elif scenario_name == 'add_redirect_uris':
# Add the new redirect URIs to the existing application
      for index, uri in enumerate(config['redirect_uris']['sign_in']):
          tf_config += f"""
          resource "okta_app_oauth_redirect_uri" "login_uri_{index}" {{
            app_id = {format_terraform_value(config['application_id'])}
            uri    = {format_terraform_value(uri)}
            type   = "LOGIN"
          }}
          """

      if 'post_logout_redirect_uris' in config and 'sign_out' in config['post_logout_redirect_uris']:
          for index, uri in enumerate(config['post_logout_redirect_uris']['sign_out']):
              tf_config += f"""
              resource "okta_app_oauth_redirect_uri" "logout_uri_{index}" {{
                app_id = {format_terraform_value(config['application_id'])}
                uri    = {format_terraform_value(uri)}
                type   = "LOGOUT"
              }}
              """

    else:
        raise ValueError(f"Unknown scenario: {scenario_name}")

    # Change back to the workflows directory
    os.chdir(os.path.dirname(__file__))

    # Write the Terraform configuration to a file
    with open('main.tf', 'w') as file:
        file.write(tf_config)

except Exception as e:
    print(f"Error: {e}")
    print("Traceback:")
    traceback.print_exc()
    sys.exit(1)
    exit(1)
