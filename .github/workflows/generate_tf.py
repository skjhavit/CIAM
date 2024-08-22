import yaml
import os

try:
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

    # Generate the Terraform configuration
    tf_config = f"""
    provider "okta" {{
      org_name   = "dev-176298"
      base_url   = "okta.com"
      api_token  = "{okta_api_token}"
    }}

    resource "okta_app_oauth" "example_app" {{
      label             = "{config['label']}"
      type              = "{config['type']}"
      grant_types       = ["implicit", "authorization_code"]
      response_types    = {config['response_types']}
      redirect_uris     = {config['redirect_uris']}
      post_logout_redirect_uris = {config.get('post_logout_redirect_uris', [])}
      token_endpoint_auth_method = "{config['token_endpoint_auth_method']}"
    }}

    resource "okta_group" "internal_users" {{
      name = "{config['groups'][0]}"
    }}

    resource "okta_group" "external_users" {{
      name = "{config['groups'][1]}"
    }}

    resource "okta_group" "deactive_users" {{
      name = "{config['groups'][2]}"
    }}

    resource "okta_app_group_assignments" "example_app_groups" {{
      app_id = okta_app_oauth.example_app.id
      group_ids = [
        okta_group.internal_users.id,
        okta_group.external_users.id,
        okta_group.deactive_users.id
      ]
    }}
    """

    # Write the Terraform configuration to a file
    with open('main.tf', 'w') as file:
        file.write(tf_config)

except Exception as e:
    print(f"Error: {e}")
    exit(1)
