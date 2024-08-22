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

    resource "okta_app_oauth" "dxp_app" {{
      label             = "{config['label']}"
      type              = "{config['type']}"
      grant_types       = ["implicit", "authorization_code"]
      response_types    = {config['response_types']}
      redirect_uris     = {config['redirect_uris']}
      post_logout_redirect_uris = {config.get('post_logout_redirect_uris', [])}
      client_uri        = "{config.get('client_uri', '')}"
      tos_uri           = "{config.get('tos_uri', '')}"
      policy_uri        = "{config.get('policy_uri', '')}"
    }}

    resource "okta_group" "internal_users" {{
      name        = "{config['groups'][0]}"
      description = "Internal users group for {config['app_name']} app"
    }}

    resource "okta_group" "external_users" {{
      name        = "{config['groups'][1]}"
      description = "External users group for {config['app_name']} app"
    }}

    resource "okta_group" "deactivated_users" {{
      name        = "{config['groups'][2]}"
      description = "Deactivated users group for {config['app_name']} app"
    }}

    resource "okta_app_group_assignments" "dxp_app_assignments" {{
      app_id = okta_app_oauth.dxp_app.id
      group {{
        id = okta_group.internal_users.id
      }}
      group {{
        id = okta_group.external_users.id
      }}
      group {{
        id = okta_group.deactivated_users.id
      }}
    }}

    output "dxp_app_client_secret" {{
      value       = okta_app_oauth.dxp_app.client_secret
      sensitive   = true
      description = "The client secret for the {config['app_name']} App"
    }}
    """

    # Write the Terraform configuration to a file
    with open('main.tf', 'w') as file:
        file.write(tf_config)

except Exception as e:
    print('lalalalalalalalaalalalalalalalalalalalalalalala')
    print(f"Error: {e}")
    print("Traceback:")
    traceback.print_exc()
    sys.exit(1)
    exit(1)