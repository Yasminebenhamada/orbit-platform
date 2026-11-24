terraform {
  required_version = ">= 1.7"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }

  # ---------------------------------------------------------------------------
  # Remote backend (Azure Blob Storage)
  #
  # Using a remote backend means:
  #  - State is stored centrally, not on a developer's laptop
  #  - Azure Blob lease-based locking prevents two concurrent `apply` runs
  #    from corrupting the state file
  #  - State is never committed to Git (it contains secrets in plain text)
  #
  # Create the storage account once by hand before enabling this block
  # (the backend cannot create the resources that store its own state):
  #
  #   az group create --name rg-tfstate --location swedencentral
  #   az storage account create \
  #     --name sttfstateorbit26 --resource-group rg-tfstate \
  #     --sku Standard_LRS --min-tls-version TLS1_2 \
  #     --allow-blob-public-access false
  #   az storage container create \
  #     --name tfstate --account-name sttfstateorbit26 --auth-mode login
  #
  # Then uncomment the block below and run `terraform init -migrate-state`
  # to move the existing local state into the remote backend.
  # ---------------------------------------------------------------------------

  # backend "azurerm" {
  #   resource_group_name  = "rg-tfstate"
  #   storage_account_name = "sttfstateorbit26"
  #   container_name       = "tfstate"
  #   key                  = "staging.terraform.tfstate"
  #   use_azuread_auth     = true
  # }
}

provider "azurerm" {
  features {}
}

module "orbit_vm" {
  source = "../../modules/vm-instance"

  name        = "orbit-staging"
  environment = "staging"
  location    = "swedencentral"
  vm_size     = "Standard_B2s_v2"

  admin_username    = "azureuser"
  ssh_public_key    = file(var.ssh_public_key_path)
  ssh_allowed_cidrs = var.ssh_allowed_cidrs

  k3s_version = "v1.30.3+k3s1"

  tags = {
    Owner   = "yasmine"
    Project = "orbit-platform"
  }
}
